# -*- coding: utf-8 -*-
"""
ResNet50 玉米病害四分类训练脚本（基线 vs 微调对比）

基线实验：冻结全部骨干，只训练 4 类分类头，Adam lr=1e-3，15 epoch，早停 patience=3
微调实验：解冻 layer4，分类头 lr=1e-3、layer4 lr=1e-4，10 epoch，早停 patience=3

产物（全部存到 outputs/）：
  outputs/baseline/  best_model.pt / history.csv / curves.png / confusion_matrix.png / classification_report.txt / metrics.json
  outputs/finetune/  同上
  outputs/compare_table.csv / compare_accuracy.png

用法：
    python train.py --mode baseline          # 只跑基线
    python train.py --mode finetune          # 只跑微调
    python train.py --mode both              # 依次跑两个实验，并生成对比表
"""

import os
import json
import time
import argparse
import random

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
from sklearn.metrics import confusion_matrix, classification_report

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from data_loader import (
    set_seed as dl_set_seed, load_cache, build_dataloaders,
    LABEL_MAP, LOCAL_CACHE_DIR,
)

# ============================================================
# 路径与常量
# ============================================================
OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
NUM_CLASSES = 4
CLASS_NAMES_CN = [LABEL_MAP[str(i)]["cn"] for i in range(NUM_CLASSES)]
CLASS_NAMES_EN = [LABEL_MAP[str(i)]["en"] for i in range(NUM_CLASSES)]

# ============================================================
# 工具函数
# ============================================================
def set_seed(seed=42):
    """固定所有随机种子，保证实验可复现"""
    dl_set_seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_device():
    """有 GPU 用 GPU，否则回落 CPU 并提示预计耗时"""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print("检测到 GPU：%s，使用 GPU 训练" % torch.cuda.get_device_name(0))
    else:
        device = torch.device("cpu")
        n = os.cpu_count() or 4
        torch.set_num_threads(max(1, n - 1))
        print("未检测到 GPU，使用 CPU 训练（%d 线程）" % torch.get_num_threads())
        print("预计耗时参考（约3852张 × ResNet50）：")
        print("  基线实验（15 epoch，只训分类头）：约 2 - 4 小时")
        print("  微调实验（10 epoch，解冻 layer4）：约 5 - 8 小时")
    return device


def build_model(mode):
    """
    构建 ResNet50 模型。
    mode = "baseline"：冻结全部骨干，只替换并训练 fc（4 类分类头）
    mode = "finetune"：在基线基础上解冻 layer4
    """
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)

    if mode == "baseline":
        # 冻结全部参数
        for param in model.parameters():
            param.requires_grad = False
    elif mode == "finetune":
        # 先全部冻结，再解冻 layer4
        for param in model.parameters():
            param.requires_grad = False
        for param in model.layer4.parameters():
            param.requires_grad = True
    else:
        raise ValueError("未知 mode：%s，应为 baseline 或 finetune" % mode)

    # 替换分类头（fc 始终可训练）
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, NUM_CLASSES)
    # 新建层默认 requires_grad=True，无需额外设置

    n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    n_total = sum(p.numel() for p in model.parameters())
    print("模型构建完成 [%s]：可训练参数 %.2fM / 总参数 %.2fM"
          % (mode, n_trainable / 1e6, n_total / 1e6))
    return model


def build_optimizer(mode, model, lr_head, lr_layer4):
    """按实验模式构建优化器（分组学习率）"""
    if mode == "baseline":
        return optim.Adam(model.fc.parameters(), lr=lr_head)
    else:  # finetune
        param_groups = [
            {"params": model.layer4.parameters(), "lr": lr_layer4},
            {"params": model.fc.parameters(), "lr": lr_head},
        ]
        return optim.Adam(param_groups, lr=lr_head)


# ============================================================
# 训练与评估循环
# ============================================================
def train_one_epoch(model, loader, criterion, optimizer, device):
    """单个 epoch 训练，返回 (avg_loss, acc)"""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        preds = outputs.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

    return running_loss / max(total, 1), correct / max(total, 1)


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    """验证/测试评估，返回 (avg_loss, acc, y_true, y_pred)"""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    y_true, y_pred = [], []
    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        preds = outputs.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)
        y_true.extend(labels.cpu().numpy().tolist())
        y_pred.extend(preds.cpu().numpy().tolist())

    return (running_loss / max(total, 1), correct / max(total, 1),
            y_true, y_pred)


# ============================================================
# 产物：训练曲线 / 混淆矩阵 / 分类报告
# ============================================================
def _set_cn_font():
    """尽量使用中文字体，缺失时退回英文标签"""
    for font in ("SimHei", "Microsoft YaHei", "SimSun", "DejaVu Sans"):
        try:
            plt.rcParams["font.sans-serif"] = [font]
            plt.rcParams["axes.unicode_minus"] = False
            return font
        except Exception:
            continue
    return None


def plot_curves(history, out_path, title):
    """绘制 train/val loss 与 acc 曲线（2 子图）"""
    _set_cn_font()
    epochs = range(1, len(history["train_loss"]) + 1)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    ax1.plot(epochs, history["train_loss"], "b-o", label="train")
    ax1.plot(epochs, history["val_loss"], "r-s", label="val")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.set_title(title + " - Loss")
    ax1.legend()
    ax1.grid(alpha=0.3)

    ax2.plot(epochs, history["train_acc"], "b-o", label="train")
    ax2.plot(epochs, history["val_acc"], "r-s", label="val")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy")
    ax2.set_title(title + " - Accuracy")
    ax2.legend()
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print("训练曲线已保存 -> %s" % out_path)


def plot_confusion_matrix(y_true, y_pred, out_path, title):
    """绘制混淆矩阵"""
    _set_cn_font()
    cm = confusion_matrix(y_true, y_pred, labels=list(range(NUM_CLASSES)))
    fig, ax = plt.subplots(figsize=(6, 5.5))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    fig.colorbar(im, ax=ax)

    tick_marks = np.arange(NUM_CLASSES)
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(CLASS_NAMES_CN, rotation=30, ha="right")
    ax.set_yticklabels(CLASS_NAMES_CN)

    thresh = cm.max() / 2.0 if cm.max() > 0 else 1
    for i in range(NUM_CLASSES):
        for j in range(NUM_CLASSES):
            ax.text(j, i, format(cm[i, j], "d"),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")

    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print("混淆矩阵已保存 -> %s" % out_path)


# ============================================================
# 主训练流程
# ============================================================
def run_experiment(mode, args, device):
    """运行单个实验（baseline 或 finetune），返回测试集 metrics"""
    out_dir = os.path.join(OUTPUTS_DIR, mode)
    os.makedirs(out_dir, exist_ok=True)
    print("\n" + "=" * 60)
    print("开始 %s 实验，输出目录：%s" % (mode.upper(), out_dir))
    print("=" * 60)

    # 数据
    splits = load_cache()
    batch_size = args.batch_size
    if device.type == "cpu" and batch_size > 16:
        batch_size = 16
        print("CPU 环境，自动将 batch_size 降为 %d" % batch_size)
    _, loaders = build_dataloaders(splits, batch_size=batch_size, num_workers=0)

    # 模型 / 损失 / 优化器
    model = build_model(mode).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = build_optimizer(mode, model, args.lr_head, args.lr_layer4)

    # 训练循环 + 早停（监控 val_acc）
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
    best_val_acc = 0.0
    best_epoch = -1
    patience_counter = 0
    best_weights_path = os.path.join(out_dir, "best_model.pt")

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(
            model, loaders["train"], criterion, optimizer, device)
        val_loss, val_acc, _, _ = evaluate(
            model, loaders["val"], criterion, device)

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        print("Epoch %2d/%d | train loss=%.4f acc=%.4f | val loss=%.4f acc=%.4f | %.0fs"
              % (epoch, args.epochs, train_loss, train_acc,
                 val_loss, val_acc, time.time() - t0))

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_epoch = epoch
            patience_counter = 0
            torch.save({
                "model_state_dict": model.state_dict(),
                "mode": mode,
                "epoch": epoch,
                "val_acc": val_acc,
                "class_names_cn": CLASS_NAMES_CN,
            }, best_weights_path)
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print("早停触发：连续 %d 个 epoch val_acc 未提升，"
                      "最佳 epoch=%d (val_acc=%.4f)"
                      % (args.patience, best_epoch, best_val_acc))
                break

    # 保存训练历史
    history_csv = os.path.join(out_dir, "history.csv")
    with open(history_csv, "w", encoding="utf-8") as f:
        f.write("epoch,train_loss,train_acc,val_loss,val_acc\n")
        for i in range(len(history["train_loss"])):
            f.write("%d,%.6f,%.6f,%.6f,%.6f\n"
                    % (i + 1, history["train_loss"][i], history["train_acc"][i],
                       history["val_loss"][i], history["val_acc"][i]))
    print("训练历史已保存 -> %s" % history_csv)
    plot_curves(history, os.path.join(out_dir, "curves.png"),
                title="%s" % mode)

    # ---------- 用最佳权重在测试集上评估 ----------
    ckpt = torch.load(best_weights_path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    test_loss, test_acc, y_true, y_pred = evaluate(
        model, loaders["test"], criterion, device)
    print("\n测试集结果：loss=%.4f, acc=%.4f（来自 epoch %d 的最佳权重）"
          % (test_loss, test_acc, ckpt["epoch"]))

    # 混淆矩阵 + 分类报告
    plot_confusion_matrix(y_true, y_pred,
                          os.path.join(out_dir, "confusion_matrix.png"),
                          title="%s Confusion Matrix" % mode)
    report = classification_report(
        y_true, y_pred,
        labels=list(range(NUM_CLASSES)),
        target_names=CLASS_NAMES_CN,
        digits=4, zero_division=0)
    report_path = os.path.join(out_dir, "classification_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print("分类报告已保存 -> %s" % report_path)
    print(report)

    # metrics.json
    metrics = {
        "mode": mode,
        "best_epoch": ckpt["epoch"],
        "best_val_acc": round(best_val_acc, 6),
        "test_loss": round(test_loss, 6),
        "test_acc": round(test_acc, 6),
        "epochs_trained": len(history["train_loss"]),
        "hyperparams": {
            "lr_head": args.lr_head,
            "lr_layer4": args.lr_layer4 if mode == "finetune" else None,
            "batch_size": batch_size,
            "max_epochs": args.epochs,
            "patience": args.patience,
            "seed": args.seed,
        },
    }
    metrics_path = os.path.join(out_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print("metrics 已保存 -> %s" % metrics_path)

    return metrics


# ============================================================
# 基线 vs 微调对比
# ============================================================
def compare_runs():
    """读取 baseline 和 finetune 的 metrics.json，生成对比表与柱状图"""
    results = {}
    for mode in ("baseline", "finetune"):
        metrics_path = os.path.join(OUTPUTS_DIR, mode, "metrics.json")
        if os.path.exists(metrics_path):
            with open(metrics_path, "r", encoding="utf-8") as f:
                results[mode] = json.load(f)

    if len(results) < 2:
        print("\n对比表需要 baseline 和 finetune 两个实验都完成，"
              "当前只有：%s" % list(results.keys()))
        return

    # 对比 CSV
    compare_csv = os.path.join(OUTPUTS_DIR, "compare_table.csv")
    with open(compare_csv, "w", encoding="utf-8") as f:
        f.write("experiment,best_epoch,epochs_trained,best_val_acc,test_acc,test_loss\n")
        for mode in ("baseline", "finetune"):
            m = results[mode]
            f.write("%s,%d,%d,%.6f,%.6f,%.6f\n"
                    % (mode, m["best_epoch"], m["epochs_trained"],
                       m["best_val_acc"], m["test_acc"], m["test_loss"]))
    print("\n基线 vs 微调对比表已保存 -> %s" % compare_csv)
    print("  baseline: test_acc=%.4f (epoch %d)" % (
        results["baseline"]["test_acc"], results["baseline"]["best_epoch"]))
    print("  finetune: test_acc=%.4f (epoch %d)" % (
        results["finetune"]["test_acc"], results["finetune"]["best_epoch"]))
    delta = results["finetune"]["test_acc"] - results["baseline"]["test_acc"]
    print("  提升幅度: %+.4f (%.2f%%)" % (delta, delta * 100))

    # 对比柱状图
    _set_cn_font()
    fig, ax = plt.subplots(figsize=(6, 4.5))
    modes = ["baseline", "finetune"]
    accs = [results[m]["test_acc"] for m in modes]
    bars = ax.bar(modes, accs, color=["#4C72B0", "#DD8452"], width=0.5)
    for bar, acc in zip(bars, accs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                "%.4f" % acc, ha="center", va="bottom")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Test Accuracy")
    ax.set_title("Baseline vs Finetune (Test Accuracy)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    compare_png = os.path.join(OUTPUTS_DIR, "compare_accuracy.png")
    fig.savefig(compare_png, dpi=150)
    plt.close(fig)
    print("对比柱状图已保存 -> %s" % compare_png)


# ============================================================
# main
# ============================================================
def parse_args():
    parser = argparse.ArgumentParser(description="ResNet50 玉米病害迁移学习训练")
    parser.add_argument("--mode", choices=["baseline", "finetune", "both"],
                        default="both", help="实验模式：基线 / 微调 / 两者")
    parser.add_argument("--epochs", type=int, default=None,
                        help="最大 epoch 数（默认：baseline=15, finetune=10）")
    parser.add_argument("--batch-size", type=int, default=16,
                        help="batch 大小（CPU 建议 <=16，GPU 可用 32）")
    parser.add_argument("--lr-head", type=float, default=1e-3,
                        help="分类头学习率")
    parser.add_argument("--lr-layer4", type=float, default=1e-4,
                        help="layer4 学习率（仅微调实验使用）")
    parser.add_argument("--patience", type=int, default=3,
                        help="早停 patience（监控 val_acc）")
    parser.add_argument("--seed", type=int, default=42,
                        help="随机种子")
    return parser.parse_args()


def main():
    args = parse_args()
    set_seed(args.seed)
    device = get_device()
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    default_epochs = {"baseline": 5, "finetune": 5}

    if args.mode in ("baseline", "both"):
        exp_args = argparse.Namespace(**vars(args))
        exp_args.epochs = args.epochs or default_epochs["baseline"]
        run_experiment("baseline", exp_args, device)

    if args.mode in ("finetune", "both"):
        exp_args = argparse.Namespace(**vars(args))
        exp_args.epochs = args.epochs or default_epochs["finetune"]
        run_experiment("finetune", exp_args, device)

    if args.mode == "both":
        compare_runs()

    print("\n全部完成。产物目录：%s" % OUTPUTS_DIR)


if __name__ == "__main__":
    main()
