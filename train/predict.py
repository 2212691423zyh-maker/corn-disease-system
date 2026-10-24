# -*- coding: utf-8 -*-
"""
单图推理脚本：加载微调好的 ResNet50，对单张玉米叶片图片输出病害中文名和置信度。

用法：
    python predict.py                          # 跑底部测试代码（随机取一张测试集图片）
    python predict.py --image 图片路径          # 推理指定图片
    python predict.py --image 图片路径 --json   # 输出 JSON，方便后端调用
"""

import os
import json
import argparse
import random

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

from data_loader import LABEL_MAP, LOCAL_CACHE_DIR

# ============================================================
# 路径与常量
# ============================================================
DEFAULT_WEIGHTS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "outputs", "finetune", "best_model.pt"
)
NUM_CLASSES = 4
CLASS_NAMES_CN = [LABEL_MAP[str(i)]["cn"] for i in range(NUM_CLASSES)]

# 推理专用 transform，与训练/测试时的评估 transform 完全一致
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
TRANSFORM = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])

# 全局缓存模型，避免重复加载
_model = None
_device = torch.device("cpu")


def load_model(weights_path=DEFAULT_WEIGHTS):
    """加载微调好的 ResNet50 权重，返回模型（eval 模式，CPU）"""
    global _model
    if _model is not None:
        return _model

    if not os.path.exists(weights_path):
        raise FileNotFoundError("模型权重不存在：%s" % weights_path)

    model = models.resnet50(weights=None)
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, NUM_CLASSES)

    ckpt = torch.load(weights_path, map_location=_device)
    state_dict = ckpt["model_state_dict"] if isinstance(ckpt, dict) and "model_state_dict" in ckpt else ckpt
    model.load_state_dict(state_dict)
    model.to(_device)
    model.eval()

    print("模型加载成功 -> %s" % weights_path)
    if isinstance(ckpt, dict):
        print("  来源实验: %s | 最佳 epoch: %s | val_acc: %s"
              % (ckpt.get("mode"), ckpt.get("epoch"), ckpt.get("val_acc")))
    _model = model
    return model


def predict(image_path, weights_path=DEFAULT_WEIGHTS, top_k=4):
    """
    对单张图片推理，返回 (病害中文名, 置信度百分比, 各类别概率列表)。

    Args:
        image_path: 玉米叶片图片路径
        weights_path: 模型权重路径（默认 outputs/finetune/best_model.pt）
        top_k: 返回前 k 个最可能类别

    Returns:
        dict: {"class_name": 中文病名, "confidence": "xx.xx%",
               "probability": 0.xxxx, "top_k": [{name, confidence, probability}, ...]}
    """
    model = load_model(weights_path)

    if not os.path.exists(image_path):
        raise FileNotFoundError("图片不存在：%s" % image_path)

    image = Image.open(image_path).convert("RGB")
    image_tensor = TRANSFORM(image).unsqueeze(0).to(_device)

    with torch.no_grad():
        outputs = model(image_tensor)
        probs = torch.softmax(outputs, dim=1)[0].cpu().numpy()

    # top-k
    top_indices = probs.argsort()[::-1][:top_k]
    top_k_list = [
        {
            "class_id": int(idx),
            "class_name": CLASS_NAMES_CN[idx],
            "probability": round(float(probs[idx]), 6),
            "confidence": "%.2f%%" % (probs[idx] * 100),
        }
        for idx in top_indices
    ]

    best_idx = top_indices[0]
    return {
        "class_name": CLASS_NAMES_CN[best_idx],
        "probability": round(float(probs[best_idx]), 6),
        "confidence": "%.2f%%" % (probs[best_idx] * 100),
        "top_k": top_k_list,
    }


# ============================================================
# 测试代码
# ============================================================
def _pick_a_test_image():
    """从本地缓存的测试集中随机取一张图片路径"""
    import json as _json
    test_cache = os.path.join(LOCAL_CACHE_DIR, "test.json")
    if not os.path.exists(test_cache):
        raise FileNotFoundError(
            "测试集缓存不存在：%s，请先运行 python data_loader.py 生成" % test_cache)
    with open(test_cache, "r", encoding="utf-8") as f:
        items = _json.load(f)
    item = random.choice(items)
    return item["path"], item["label"]


def main():
    parser = argparse.ArgumentParser(description="玉米病害模型推理")
    parser.add_argument("--image", type=str, default=None,
                        help="图片路径；不指定则随机取一张测试集图片")
    parser.add_argument("--weights", type=str, default=DEFAULT_WEIGHTS,
                        help="模型权重路径")
    parser.add_argument("--json", action="store_true",
                        help="以 JSON 格式输出，方便后端解析")
    args = parser.parse_args()

    if args.image:
        image_path = args.image
        true_label = None
    else:
        image_path, true_label = _pick_a_test_image()
        print("随机测试图片：%s" % image_path)
        if true_label is not None:
            print("真实标签: [%d] %s" % (true_label, CLASS_NAMES_CN[true_label]))

    result = predict(image_path, weights_path=args.weights)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n" + "=" * 40)
        print("预测结果：%s" % result["class_name"])
        print("置信度：%s" % result["confidence"])
        print("-" * 40)
        print("各类别概率：")
        for item in result["top_k"]:
            print("  [%d] %-10s %s" % (item["class_id"], item["class_name"], item["confidence"]))
        print("=" * 40)


if __name__ == "__main__":
    main()
