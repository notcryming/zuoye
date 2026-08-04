import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForTokenClassification, TrainingArguments, Trainer, DataCollatorForTokenClassification
import evaluate
import numpy as np
import json


dataset = load_dataset("json", data_files={"train": "train.json"})

with open("label.json", "r", encoding="utf-8") as f:
    label_dict = json.load(f)
label_list = [""] * len(label_dict)
for k, v in label_dict.items():
    label_list[v] = k
# print(label_list)

small_data = dataset["train"].select(range(int(len(dataset["train"]) * 0.05)))
split_data = small_data.train_test_split(train_size=0.8, seed=42)
dataset["train"] = split_data["train"]
dataset["validation"] = split_data["test"]

print("训练数据量，", len(dataset["train"]))
print("验证数据量，", len(dataset["validation"]))

model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(
    model_name, num_labels=len(label_list)
)

def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(examples["tokens"], truncation=True, is_split_into_words=True)
    labels = []
    for i, label in enumerate(examples["tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            else:
                label_ids.append(label[word_idx])
        labels.append(label_ids)
    tokenized_inputs["labels"] = labels
    return tokenized_inputs




