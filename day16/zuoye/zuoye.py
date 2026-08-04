import torch
from datasets import load_dataset
from transformers import AutoTokenizer, BertForSequenceClassification, TrainingArguments, Trainer, DataCollatorWithPadding
import evaluate
import numpy as np

# 1.加载数据集
dataset = load_dataset("json", data_files={
    "train": "yelp_train.json",
    "test": "yelp_test.json"
})

# 数据量太大，采样固定数量加速训练
train_total = 6250   # 切8:2后刚好训练集5000条，验证集1250条
test_total = 1250
small_train = dataset["train"].select(range(train_total))
small_test = dataset["test"].select(range(test_total))

# 从采样后的训练集中划分出验证集
split_data = small_train.train_test_split(train_size=0.8, seed=42)
dataset["train"] = split_data["train"]
dataset["validation"] = split_data["test"]
dataset["test"] = small_test

print("训练数据量：", len(dataset["train"]))
print("验证数据量：", len(dataset["validation"]))
print("测试数据量：", len(dataset["test"]))

# 2.加载分词器和模型
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = BertForSequenceClassification.from_pretrained(
    model_name, num_labels=2
)

# 3.数据预处理
def tokenize_function(examples):
    tokenized_inputs = tokenizer(examples["text"], truncation=True)
    tokenized_inputs["labels"] = examples["label"]
    return tokenized_inputs

tokenized_dataset = dataset.map(tokenize_function, batched=True)

# 4.评估函数
metric = evaluate.load("accuracy")
def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=-1)
    results = metric.compute(predictions=predictions, references=labels)
    return {"accuracy": results["accuracy"]}

# 5.训练参数
training_args = TrainingArguments(
    output_dir="./bert_clf_demo",
    per_device_train_batch_size=16,
    num_train_epochs=2,
    eval_strategy="epoch",
    learning_rate=2e-5,
    logging_steps=10,
    save_strategy="no"
)

# 6.开始训练
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["validation"],
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)
trainer.train()

# 评估测试集
print("\n在测试集上评估：")
test_results = trainer.evaluate(eval_dataset=tokenized_dataset["test"])
print("测试集结果：", test_results)

# 7.保存模型和分词器
save_path = "./bert_clf_saved_model"
model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)
print(f"\n模型已保存到: {save_path}")

# ========================三个测试用例====================
print("\n正在从本地加载模型进行测试...")
tokenizer = AutoTokenizer.from_pretrained(save_path)
model = BertForSequenceClassification.from_pretrained(save_path)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.eval()
model.to(device)

def clf_infer(sent):
    inputs = tokenizer(sent, return_tensors="pt", truncation=True).to(device)
    with torch.no_grad():
        logits = model(**inputs).logits
    pred_id = torch.argmax(logits, dim=-1)[0].cpu().item()
    label = "正面" if pred_id == 1 else "负面"
    return label

# 3条课堂测试句子
test_texts = [
    "The food was great and the service was excellent!",
    "Terrible experience, the staff was rude and slow.",
    "It was okay, nothing special but not bad either."
]

print("\n" + "="*50)
print("BERT 文本分类模型测试结果")
print("="*50)
for idx, text in enumerate(test_texts, 1):
    print(f"测试样例{idx}：{text}")
    print(f"预测情感：{clf_infer(text)}\n")
