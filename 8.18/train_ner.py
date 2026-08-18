# -*- coding: utf-8 -*-
"""
基于 bert-base-chinese 的中文 NER 训练脚本
数据集: RICAR03/cluener2020 (HuggingFace, CLUENER2020, 10 类实体 BIO)
输出: 训练过程的 loss + 验证集整体 P/R/F1 + 每类实体分类报告
"""
import os
import sys

# 沙箱限制: 依赖安装在项目内 pylibs, 且禁用用户级 site-packages(有损坏的 pyarrow)
os.environ["PYTHONNOUSERSITE"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pylibs"))

import numpy as np
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification,
)
from seqeval.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)

MODEL_NAME = "bert-base-chinese"
DATA_NAME = "RICAR03/cluener2020"
MAX_LEN = 128
BATCH_SIZE = 32
EPOCHS = 3
LR = 2e-5
SEED = 42
OUTPUT_DIR = "ner_bert_base_chinese"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    # ---------- 1. 加载数据 ----------
    print(">> 加载数据集", DATA_NAME)
    ds = load_dataset(DATA_NAME)["train"]
    # CLUENER2020 只有 train, 按 9:1 划分训练/验证
    split = ds.train_test_split(test_size=0.1, seed=SEED)
    train_ds, eval_ds = split["train"], split["test"]
    print(f"  训练样本: {len(train_ds)}  验证样本: {len(eval_ds)}")

    label_names = ds.features["ner_tags"].feature.names  # 21 个标签
    id2label = {i: n for i, n in enumerate(label_names)}
    label2id = {n: i for i, n in enumerate(label_names)}
    print(f"  标签数: {len(label_names)}")
    print(f"  标签: {label_names}")

    # ---------- 2. 分词 + 标签对齐 ----------
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize_and_align(examples):
        tokenized = tokenizer(
            examples["tokens"],
            truncation=True,
            max_length=MAX_LEN,
            is_split_into_words=True,
        )
        labels = []
        for i, tags in enumerate(examples["ner_tags"]):
            word_ids = tokenized.word_ids(batch_index=i)
            label_ids = []
            prev = None
            for wid in word_ids:
                if wid is None:          # [CLS]/[SEP]/[PAD]
                    label_ids.append(-100)
                elif wid != prev:        # 每个词的第一个 sub-token 保留标签
                    label_ids.append(tags[wid])
                else:                    # 后续 sub-token 忽略
                    label_ids.append(-100)
                prev = wid
            labels.append(label_ids)
        tokenized["labels"] = labels
        return tokenized

    cols = ["id", "tokens", "ner_tags"]
    train_enc = train_ds.map(tokenize_and_align, batched=True, remove_columns=cols)
    eval_enc = eval_ds.map(tokenize_and_align, batched=True, remove_columns=cols)

    # ---------- 3. 模型 ----------
    model = AutoModelForTokenClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(label_names),
        id2label=id2label,
        label2id=label2id,
    )

    # ---------- 4. 评估指标 (seqeval) ----------
    def compute_metrics(p):
        preds, labels = p
        preds = np.argmax(preds, axis=-1)
        true_labels, true_preds = [], []
        for p_seq, l_seq in zip(preds, labels):
            p_tags, l_tags = [], []
            for p_id, l_id in zip(p_seq, l_seq):
                if l_id == -100:
                    continue
                p_tags.append(id2label[p_id])
                l_tags.append(id2label[l_id])
            true_preds.append(p_tags)
            true_labels.append(l_tags)
        return {
            "accuracy": accuracy_score(true_labels, true_preds),
            "precision": precision_score(true_labels, true_preds),
            "recall": recall_score(true_labels, true_preds),
            "f1": f1_score(true_labels, true_preds),
        }

    # ---------- 5. 训练 ----------
    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)
    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        learning_rate=LR,
        weight_decay=0.01,
        warmup_steps=0,
        lr_scheduler_type="linear",
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        logging_strategy="steps",
        logging_steps=50,
        seed=SEED,
        metric_for_best_model="f1",
        greater_is_better=True,
        load_best_model_at_end=True,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_enc,
        eval_dataset=eval_enc,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    print(">> 开始训练 ...")
    trainer.train()

    # ---------- 6. 最终评估 ----------
    print("\n" + "=" * 60)
    print("验证集整体指标 (seqeval)")
    print("=" * 60)
    metrics = trainer.evaluate(eval_dataset=eval_enc)
    for k, v in metrics.items():
        print(f"  {k}: {v:.6f}" if isinstance(v, float) else f"  {k}: {v}")

    # 每类实体的分类报告
    preds = trainer.predict(eval_enc)
    pred_labels = np.argmax(preds.predictions, axis=-1)
    true_labels, true_preds = [], []
    for p_seq, l_seq in zip(pred_labels, preds.label_ids):
        p_tags, l_tags = [], []
        for p_id, l_id in zip(p_seq, l_seq):
            if l_id == -100:
                continue
            p_tags.append(id2label[p_id])
            l_tags.append(id2label[l_id])
        true_preds.append(p_tags)
        true_labels.append(l_tags)

    print("\n" + "=" * 60)
    print("每类实体详细指标")
    print("=" * 60)
    print(classification_report(true_labels, true_preds, digits=4))

    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"\n>> 模型已保存到 {os.path.abspath(OUTPUT_DIR)}")


if __name__ == "__main__":
    main()
