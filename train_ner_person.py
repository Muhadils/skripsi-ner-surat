import json
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, TrainingArguments, Trainer, AutoConfig
from transformers import DataCollatorForTokenClassification
from datasets import Dataset
import os
from torch import nn

# 1. Konfigurasi Khusus (Hanya PERSON)
model_name = "indobenchmark/indobert-lite-base-p2"
label_list = ["O", "B-PERSON", "I-PERSON"] # Hanya 3 label agar fokus
label2id = {label: i for i, label in enumerate(label_list)}
id2label = {i: label for i, label in enumerate(label_list)}

tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

# KUSTOM TRAINER UNTUK WEIGHTED LOSS
class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        
        # Beri bobot tinggi (15.0) pada B-PERSON dan I-PERSON
        # Ini memaksa model untuk tidak malas dan tidak menganggap semuanya sebagai 'O'
        weights = torch.tensor([1.0, 15.0, 15.0]).to(logits.device)
        
        loss_fct = nn.CrossEntropyLoss(weight=weights)
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss

def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(
        examples["text"], truncation=True, padding="max_length", max_length=512, return_offsets_mapping=True 
    )
    
    labels = []
    for i, example_entities in enumerate(examples["entities"]):
        offset_mapping = tokenized_inputs["offset_mapping"][i]
        label_ids = [0] * len(tokenized_inputs["input_ids"][i])
        
        for ent in example_entities:
            # FILTER: Hanya proses label PERSON, abaikan yang lain
            if ent["label"] != "PERSON":
                continue
                
            start, end = ent["start"], ent["end"]
            for idx, (t_start, t_end) in enumerate(offset_mapping):
                if t_start == t_end == 0: continue 
                if t_start < end and t_end > start:
                    if t_start == start: 
                        label_ids[idx] = label2id["B-PERSON"]
                    else: 
                        label_ids[idx] = label2id["I-PERSON"]
        labels.append(label_ids)
    
    tokenized_inputs["labels"] = labels
    tokenized_inputs.pop("offset_mapping")
    return tokenized_inputs

import numpy as np
from sklearn.metrics import precision_recall_fscore_support, accuracy_score

def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    # Hilangkan index -100 (padding)
    true_predictions = [
        [id2label[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [id2label[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    # Ratakan list
    flat_true_labels = [item for sublist in true_labels for item in sublist]
    flat_true_preds = [item for sublist in true_predictions for item in sublist]

    precision, recall, f1, _ = precision_recall_fscore_support(flat_true_labels, flat_true_preds, average='weighted', zero_division=0)
    acc = accuracy_score(flat_true_labels, flat_true_preds)
    
    return {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }

def main():
    print("--- MEMULAI PELATIHAN MODEL TERPISAH (PERSON) ---")
    # ... (kode sebelumnya) ...
    
    # Pisahkan data untuk evaluasi (Validation Set)
    split_data = dataset.train_test_split(test_size=0.15)
    train_dataset = split_data['train'].map(tokenize_and_align_labels, batched=True)
    eval_dataset = split_data['test'].map(tokenize_and_align_labels, batched=True)

    training_args = TrainingArguments(
        output_dir="./results_person",
        num_train_epochs=10,
        per_device_train_batch_size=8,
        evaluation_strategy="epoch", # Evaluasi setiap epoch
        learning_rate=3e-5,
        save_total_limit=1,
        use_cpu=True,
        logging_steps=10
    )

    trainer = WeightedTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset, # Tambahkan eval dataset
        data_collator=DataCollatorForTokenClassification(tokenizer),
        compute_metrics=compute_metrics # Tambahkan metrik
    )

    print("Melatih...")
    trainer.train()
    
    # Simpan di folder khusus PERSON
    output_dir = "./model_ner_person"
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"SELESAI! Model PERSON disimpan di: {output_dir}")

if __name__ == "__main__":
    main()
