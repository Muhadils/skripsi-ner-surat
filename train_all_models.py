#!/usr/bin/env python3
"""
MASTER TRAINING SCRIPT - Train all NER models at once
Skripsi Nurfadilah Rahman - NLP & NER untuk Pembuatan Teks Otomatis
"""

import json
import torch
import os
import sys
from pathlib import Path
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification
)
from datasets import Dataset
import numpy as np
from sklearn.metrics import precision_recall_fscore_support, accuracy_score
from torch import nn

print("="*70)
print("  MASTER NER TRAINING SCRIPT - SKRIPSI NURFADILAH RAHMAN")
print("="*70)

# ==================== KONFIGURASI ====================
LOCAL_PATH = "./indobert-base-local"
MODEL_NAME = LOCAL_PATH if os.path.exists(LOCAL_PATH) else "indobenchmark/indobert-lite-base-p2"

# Definisi 4 model NER terpisah
NER_CONFIGS = {
    "PERSON": {
        "output_dir": "./model_ner_person",
        "labels": ["O", "B-PERSON", "I-PERSON"],
        "description": "Ekstraksi nama orang"
    },
    "NIK": {
        "output_dir": "./model_ner_nik",
        "labels": ["O", "B-NIK", "I-NIK"],
        "description": "Ekstraksi nomor identitas (NIK)"
    },
    "PROFIL": {
        "output_dir": "./model_ner_profil",
        "labels": ["O", "B-ALAMAT", "I-ALAMAT", "B-KERJA", "I-KERJA", "B-TGL", "I-TGL", "B-JABATAN", "I-JABATAN"],
        "description": "Ekstraksi profil: Alamat, Pekerjaan, Tanggal, Jabatan"
    },
    "LUAS_HARGA": {
        "output_dir": "./model_ner_luas_harga",
        "labels": ["O", "B-LUAS", "I-LUAS", "B-HARGA", "I-HARGA"],
        "description": "Ekstraksi luas dan harga tanah"
    }
}

print(f"\n✓ Menggunakan model base: {MODEL_NAME}")
print(f"✓ Akan melatih {len(NER_CONFIGS)} model NER\n")

# ==================== LOAD DATASET ====================
def load_dataset(json_file="dataset_ner.json"):
    """Load training data dari JSON"""
    if not os.path.exists(json_file):
        print(f"❌ Error: File {json_file} tidak ditemukan!")
        sys.exit(1)

    with open(json_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    print(f"✓ Dataset loaded: {len(raw_data)} samples")
    return raw_data

# ==================== FILTER DATA PER MODEL ====================
def filter_data_for_model(raw_data, target_labels):
    """Filter data yang relevan untuk specific model"""
    filtered = []
    for sample in raw_data:
        entities_filtered = [e for e in sample['entities'] if e['label'] in target_labels]
        if entities_filtered:  # Hanya ambil samples yang punya entities
            filtered.append({
                "text": sample['text'],
                "entities": entities_filtered
            })
    return filtered

# ==================== WEIGHTED TRAINER ====================
class WeightedTrainer(Trainer):
    """Custom trainer dengan class weights untuk handle imbalance"""
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")

        # Class weights: prioritize entity labels over O (no-entity)
        weights = torch.ones(len(self.model.config.id2label))
        weights[0] = 1.0  # O label weight
        for i in range(1, len(weights)):
            weights[i] = 10.0  # Entity labels weight

        weights = weights.to(logits.device)
        loss_fct = nn.CrossEntropyLoss(weight=weights)
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))

        return (loss, outputs) if return_outputs else loss

# ==================== METRICS COMPUTATION ====================
def compute_metrics(p, id2label):
    """Compute precision, recall, F1-score"""
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    true_predictions = [
        [id2label[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [id2label[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    flat_true_labels = [item for sublist in true_labels for item in sublist]
    flat_true_preds = [item for sublist in true_predictions for item in sublist]

    precision, recall, f1, _ = precision_recall_fscore_support(
        flat_true_labels, flat_true_preds,
        average='weighted', zero_division=0
    )
    accuracy = accuracy_score(flat_true_labels, flat_true_preds)

    return {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1}

# ==================== TOKENIZATION & ALIGNMENT ====================
def tokenize_and_align_labels(examples, tokenizer, label2id, target_labels):
    """Tokenize text dan align labels dengan tokens"""
    tokenized_inputs = tokenizer(
        examples["text"],
        truncation=True,
        padding="max_length",
        max_length=512,
        return_offsets_mapping=True
    )

    labels = []
    for i, example_entities in enumerate(examples["entities"]):
        offset_mapping = tokenized_inputs["offset_mapping"][i]
        label_ids = [0] * len(tokenized_inputs["input_ids"][i])

        for ent in example_entities:
            if ent["label"] not in target_labels:
                continue

            ent_label = ent["label"]
            char_start = ent["start"]
            char_end = ent["end"]

            token_start_idx = None
            token_end_idx = None

            for idx, (token_start, token_end) in enumerate(offset_mapping):
                if token_start_idx is None and token_start >= char_start:
                    token_start_idx = idx
                if token_start >= char_end:
                    token_end_idx = idx
                    break

            if token_start_idx is None:
                token_start_idx = 0
            if token_end_idx is None:
                token_end_idx = len(offset_mapping)

            # Assign B- dan I- labels
            for token_idx in range(token_start_idx, token_end_idx):
                if token_idx == token_start_idx:
                    label_ids[token_idx] = label2id[f"B-{ent_label}"]
                else:
                    label_ids[token_idx] = label2id[f"I-{ent_label}"]

        labels.append(label_ids)

    tokenized_inputs.pop("offset_mapping", None)
    tokenized_inputs["labels"] = labels
    return tokenized_inputs

# ==================== MAIN TRAINING LOGIC ====================
def train_model(model_name, config, raw_data):
    """Train single NER model"""
    print(f"\n{'='*70}")
    print(f"  TRAINING: {model_name} - {config['description']}")
    print(f"  Output: {config['output_dir']}")
    print(f"{'='*70}")

    # Filter data for this model
    label_list = config['labels']
    label2id = {label: i for i, label in enumerate(label_list)}
    id2label = {i: label for i, label in enumerate(label_list)}
    target_labels = set(label.split('-')[1] for label in label_list if '-' in label)

    model_data = filter_data_for_model(raw_data, target_labels)
    if not model_data:
        print(f"⚠️  SKIP: No training data found for {model_name}")
        return False

    print(f"✓ Training samples: {len(model_data)}")

    # Split train/eval (80-20)
    train_size = int(0.8 * len(model_data))
    train_data = model_data[:train_size]
    eval_data = model_data[train_size:]

    print(f"  - Train: {len(train_data)}, Eval: {len(eval_data)}")

    # Create Hugging Face Dataset
    train_dataset = Dataset.from_dict({
        "text": [s["text"] for s in train_data],
        "entities": [s["entities"] for s in train_data]
    })
    eval_dataset = Dataset.from_dict({
        "text": [s["text"] for s in eval_data],
        "entities": [s["entities"] for s in eval_data]
    })

    # Load tokenizer & model
    print(f"✓ Loading tokenizer & model...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
    model = AutoModelForTokenClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(label_list),
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True
    )

    # Tokenize
    tokenizer_fn = lambda x: tokenize_and_align_labels(x, tokenizer, label2id, target_labels)
    train_dataset = train_dataset.map(tokenizer_fn, batched=True, remove_columns=train_dataset.column_names)
    eval_dataset = eval_dataset.map(tokenizer_fn, batched=True, remove_columns=eval_dataset.column_names)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=config['output_dir'],
        eval_strategy="epoch",
        learning_rate=5e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=3,
        weight_decay=0.01,
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        push_to_hub=False,
        logging_steps=20,
        save_total_limit=2,
    )

    # Data collator
    data_collator = DataCollatorForTokenClassification(tokenizer)

    # Trainer with custom metrics
    trainer = WeightedTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        compute_metrics=lambda p: compute_metrics(p, id2label),
    )

    # Train
    print(f"✓ Starting training...")
    trainer.train()

    # Save
    print(f"✓ Saving model...")
    model.save_pretrained(config['output_dir'])
    tokenizer.save_pretrained(config['output_dir'])

    # Final eval
    eval_results = trainer.evaluate()
    print(f"\n  📊 Final Evaluation Metrics:")
    print(f"     Accuracy:  {eval_results.get('eval_accuracy', 0):.4f}")
    print(f"     Precision: {eval_results.get('eval_precision', 0):.4f}")
    print(f"     Recall:    {eval_results.get('eval_recall', 0):.4f}")
    print(f"     F1-Score:  {eval_results.get('eval_f1', 0):.4f}")

    return True

# ==================== MAIN ====================
if __name__ == "__main__":
    raw_data = load_dataset()

    results = {}
    for model_key, model_config in NER_CONFIGS.items():
        try:
            success = train_model(model_key, model_config, raw_data)
            results[model_key] = "✅ SUCCESS" if success else "⏭️  SKIPPED"
        except Exception as e:
            print(f"❌ ERROR training {model_key}: {e}")
            results[model_key] = f"❌ ERROR: {str(e)[:50]}"

    # Summary
    print(f"\n{'='*70}")
    print("  TRAINING SUMMARY")
    print(f"{'='*70}")
    for model_key, status in results.items():
        print(f"  {model_key:15} → {status}")

    print(f"\n✅ Training batch completed!")
    print(f"📌 Next step: Run extract_final.py untuk test extraction")
