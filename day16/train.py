import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForTokenClassification, TrainingArguments, Trainer, DataCollatorForTokenClassification
import evaluate
import numpy as np
import json

#1.加载数据集
dataset = load_dataset("json", data_files={"train": "train.json"})

with open("label.json", "r", encoding="utf-8") as f:
    label_dict = json.load(f)
label_list = [""] * len(label_dict)
for k, v in label_dict.items():
    label_list[v] = k
# print(label_list)

small_data = dataset["train"].select(range(int(len(dataset["train"]) * 1)))
split_data = small_data.train_test_split(train_size=0.8, seed=42) 
dataset["train"] = split_data["train"]
dataset["validation"] = split_data["test"]

print("训练数据量：", len(dataset["train"]))  
print("验证数据量：", len(dataset["validation"]))  

#2.加载分词器和模型
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(
    model_name, num_labels=len(label_list)
)

# 3. 数据预处理
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

tokenized_dataset = dataset.map(tokenize_and_align_labels, batched=True)

# 4.评估函数
metric = evaluate.load("seqeval")
def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)
    true_predictions = [[label_list[p] for (p, l) in zip(prediction, label) if l != -100] for prediction, label in zip(predictions, labels)]
    true_labels = [[label_list[l] for (p, l) in zip(prediction, label) if l != -100] for prediction, label in zip(predictions, labels)]
    results = metric.compute(predictions=true_predictions, references=true_labels)
    return {"f1": results["overall_f1"]}

# 5.训练参数
training_args = TrainingArguments(
    output_dir="./bert_ner_demo",
    per_device_train_batch_size=8,
    num_train_epochs=3,
    eval_strategy="epoch",
    learning_rate=2e-5,
    logging_steps=10,
    save_strategy="no"
)

# 6.开始训练
data_collator = DataCollatorForTokenClassification(tokenizer)  #源代码，数据增强？
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["validation"],
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)
trainer.train()

# 7.保存模型和分词器
save_path = "./bert_ner_saved_model_new"
model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)
print(f"\n模型已保存到: {save_path}")

#========================三个测试用例====================
print("\n正在从本地加载模型进行测试...")
tokenizer = AutoTokenizer.from_pretrained(save_path)
model = AutoModelForTokenClassification.from_pretrained(save_path)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.eval()
model.to(device)

def ner_infer(sent):
    inputs = tokenizer(sent, return_tensors="pt", truncation=True).to(device)
    with torch.no_grad():
        logits = model(**inputs).logits
    pred_ids = torch.argmax(logits, dim=-1)[0].cpu().tolist()
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
    res = []
    for tok, tid in zip(tokens, pred_ids):
        tag = label_list[tid]
        if tag != "O" and tok not in ("[CLS]", "[SEP]"):
            res.append(f"{tok}->{tag}")
    return res

# 3条课堂测试句子
test_texts = [
    "Jack lives in Beijing",
    "Tencent is a big company",
    "Alice will go to Shanghai tomorrow"
]

print("\n" + "="*50)
print("BERT-NER 模型测试结果")
print("="*50)
for idx, text in enumerate(test_texts,1):
    print(f"测试样例{idx}：{text}")
    print(f"识别实体：{ner_infer(text)}\n")