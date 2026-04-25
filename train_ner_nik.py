import json
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, TrainingArguments, Trainer, AutoConfig
from transformers import DataCollatorForTokenClassification
from datasets import Dataset
import os
from torch import nn
import numpy as np
from sklearn.metrics import precision_recall_fscore_support, accuracy_score

# 1. Konfigurasi Khusus (Hanya NIK)
model_name = "indobenchmark/indobert-lite-base-p2"
label_list = ["O", "B-NIK", "I-NIK"]
label2id = {label: i for i, label in enumerate(label_list)}
id2label = {i: label for i, label in enumerate(label_list)}

tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        weights = torch.tensor([1.0, 20.0, 20.0]).to(logits.device) # Bobot lebih tinggi karena NIK sangat spesifik
        loss_fct = nn.CrossEntropyLoss(weight=weights)
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss

def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)
    true_predictions = [[id2label[p] for (p, l) in zip(prediction, label) if l != -100] for prediction, label in zip(predictions, labels)]
    true_labels = [[id2label[l] for (p, l) in zip(prediction, label) if l != -100] for prediction, label in zip(predictions, labels)]
    flat_true_labels = [item for sublist in true_labels for item in sublist]
    flat_true_preds = [item for sublist in true_predictions for item in sublist]
    precision, recall, f1, _ = precision_recall_fscore_support(flat_true_labels, flat_true_preds, average='weighted', zero_division=0)
    return {"accuracy": accuracy_score(flat_true_labels, flat_true_preds), "precision": precision, "recall": recall, "f1": f1}

def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(examples["text"], truncation=True, padding="max_length", max_length=512, return_offsets_mapping=True)
    labels = []
    for i, example_entities in enumerate(examples["entities"]):
        offset_mapping = tokenized_inputs["offset_mapping"][i]
        label_ids = [0] * len(tokenized_inputs["input_ids"][i])
        for ent in example_entities:
            if ent["label"] != "NIK": continue
            start, end = ent["start"], ent["end"]
            for idx, (t_start, t_end) in enumerate(offset_mapping):
                if t_start == t_end == 0: continue 
                if t_start < end and t_end > start:
                    if t_start == start: label_ids[idx] = label2id["B-NIK"]
                    else: label_ids[idx] = label2id["I-NIK"]
        labels.append(label_ids)
    tokenized_inputs["labels"] = labels
    return tokenized_inputs

def main():
    print("--- MEMULAI PELATIHAN MODEL TERPISAH (NIK) ---")
    with open('dataset_ner.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    with_ent = [d for d in raw_data if any(e['label'] == 'NIK' for e in d['entities'])]
    without_ent = [d for d in raw_data if not any(e['label'] == 'NIK' for e in d['entities'])]
    final_data = with_ent + without_ent[:20]
    dataset = Dataset.from_list(final_data).train_test_split(test_size=0.15)
    train_dataset = dataset['train'].map(tokenize_and_align_labels, batched=True)
    eval_dataset = dataset['test'].map(tokenize_and_align_labels, batched=True)
    config = AutoConfig.from_pretrained(model_name, num_labels=3, id2label=id2label, label2id=label2id)
    model = AutoModelForTokenClassification.from_pretrained(model_name, config=config, ignore_mismatched_sizes=True)
    training_args = TrainingArguments(output_dir="./results_nik", num_train_epochs=10, per_device_train_batch_size=8, eval_strategy="epoch", learning_rate=3e-5, save_strategy="no", use_cpu=True)
    trainer = Trainer(model=model, args=training_args, train_dataset=train_dataset, eval_dataset=eval_dataset, data_collator=DataCollatorForTokenClassification(tokenizer), compute_metrics=compute_metrics)
    trainer.train()
    model.save_pretrained("./model_ner_nik"); tokenizer.save_pretrained("./model_ner_nik")
    print("SELESAI! Model NIK disimpan di: ./model_ner_nik")

if __name__ == "__main__":
    main()
