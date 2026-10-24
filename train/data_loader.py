# -*- coding: utf-8 -*-
"""
数据加载模块（本地文件夹版，不再依赖 HuggingFace）

数据源：d:\\bs\\train\\data\\plantvillage dataset\\color
仅读取 4 个玉米文件夹，硬编码标签映射（用户明确指定）。

leaf_id 划分策略：
  - 文件名前缀匹配 UUID 格式（xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx）
    则用该 UUID 作为 leaf_id，按 leaf_id 7:1.5:1.5 划分
  - 否则退化为按图片随机划分（固定 seed=42），打印警告

用法：
    python data_loader.py                    # 首次：读取本地文件夹 -> 划分 -> 保存
    python data_loader.py --use_local_cache  # 后续：直接加载本地缓存
"""

import os
import json
import re
import argparse
import random
from collections import Counter, defaultdict

import numpy as np
from PIL import Image
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import transforms

# ============================================================
# 路径与标签映射（硬编码，用户明确指定）
# ============================================================
DATA_ROOT = r"d:\bs\train\data\plantvillage dataset\color"
CORN_SUBDIRS = {
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": 0,   # 灰斑病
    "Corn_(maize)___Common_rust_": 1,                            # 普通锈病
    "Corn_(maize)___Northern_Leaf_Blight": 2,                    # 北方叶枯病
    "Corn_(maize)___healthy": 3,                                  # 健康叶片
}
LABEL_MAP = {
    "0": {"cn": "灰斑病", "en": "Gray_leaf_spot"},
    "1": {"cn": "普通锈病", "en": "Common_rust"},
    "2": {"cn": "北方叶枯病", "en": "Northern_Leaf_Blight"},
    "3": {"cn": "健康叶片", "en": "healthy"},
}
EXPECTED_COUNTS = {"灰斑病": 513, "普通锈病": 1192, "北方叶枯病": 985, "健康叶片": 1162}
LOCAL_CACHE_DIR = r"d:\bs\train\data\corn_subset"
LABEL_MAP_PATH = r"d:\bs\train\data\label_map.json"

TRAIN_RATIO, VAL_RATIO, TEST_RATIO = 0.70, 0.15, 0.15
SEED = 42

# UUID 正则：文件名中第一个 ___ 前缀（xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx）
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

# ============================================================
# 数据增强：ImageNet 均值方差，Resize + RandomCrop / CenterCrop
# ============================================================
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_transforms(split="train"):
    """根据 split 返回对应的 torchvision transform"""
    if split == "train":
        return transforms.Compose([
            transforms.Resize(256),
            transforms.RandomCrop(224),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.02),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])
    else:  # val / test
        return transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])


# ============================================================
# 辅助：固定随机种子 / 解析 leaf_id
# ============================================================
def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)


def parse_leaf_id(filename):
    """
    从文件名解析 leaf_id。
    PlantVillage 命名：UUID___描述  或  RS_xxx 编号描述（无 UUID）
    返回 (leaf_id, method)：
      - 若前缀匹配 UUID 格式：返回 (uuid, "uuid")
      - 否则返回 (None, "fallback") 表示无法解析
    """
    # 按 ___ 分割，取第一段
    if "___" in filename:
        prefix = filename.split("___")[0].strip()
        if UUID_PATTERN.match(prefix):
            return prefix, "uuid"
    return None, "fallback"


# ============================================================
# 扫描：收集 4 个文件夹的全部图片，解析 leaf_id
# ============================================================
def scan_corn_images():
    """
    扫描 4 个玉米文件夹，返回 list[(filepath, label_id, leaf_id, parse_method)]
    """
    results = []
    all_methods = Counter()

    for folder_name, label_id in CORN_SUBDIRS.items():
        folder_path = os.path.join(DATA_ROOT, folder_name)
        if not os.path.isdir(folder_path):
            print("错误：文件夹不存在 -> %s" % folder_path)
            continue

        cn_name = LABEL_MAP[str(label_id)]["cn"]
        count_before = len(results)

        for fname in os.listdir(folder_path):
            fpath = os.path.join(folder_path, fname)
            if not os.path.isfile(fpath):
                continue
            if not fname.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
                continue

            leaf_id, method = parse_leaf_id(fname)
            results.append((fpath, label_id, leaf_id, method))
            all_methods[method] += 1

        n_class = len(results) - count_before
        expected = EXPECTED_COUNTS.get(cn_name, None)
        status = ""
        if expected is not None and abs(n_class - expected) > 50:
            status = "  [警告：样本数 %d 与预期 %d 偏差较大]" % (n_class, expected)
        print("  [%d] %s (%-45s): 发现 %d 张图片%s"
              % (label_id, cn_name, folder_name, n_class, status))

    print("\nleaf_id 解析统计：uuid=%d, fallback=%d"
          % (all_methods.get("uuid", 0), all_methods.get("fallback", 0)))

    # 若 fallback 类存在，说明至少有一个文件夹无法按 leaf_id 分组
    if all_methods.get("fallback", 0) > 0:
        print("""
==================== 警告 ====================
部分/全部玉米文件夹无法从文件名解析 UUID leaf_id，
已退化为按图片随机划分。可能存在同一片叶子多角度照片跨集泄漏的风险，
论文中需注明此退化划分方式及潜在的数据泄漏风险。
===============================================""")

    return results


# ============================================================
# 划分：按 label_id 独立划分，label 内部再按 leaf_id 或随机
# ============================================================
def split_by_class(records, seed=SEED):
    """
    逐类别划分（避免跨类别，保证每个类别在各 split 都有样本）。
    返回 dict: "train"/"val"/"test" -> list[(fpath, label_id)]
    """
    set_seed(seed)

    splits = {"train": [], "val": [], "test": []}

    # 按 label_id 分组
    by_label = defaultdict(list)
    for rec in records:
        fpath, lid, leaf_id, method = rec
        by_label[lid].append(rec)

    for label_id, class_records in by_label.items():
        cn_name = LABEL_MAP[str(label_id)]["cn"]

        # 收集 leaf_id
        leaf_groups = defaultdict(list)
        fallback_records = []
        has_uuid = False

        for rec in class_records:
            fpath, lid, leaf_id, method = rec
            if method == "uuid" and leaf_id is not None:
                leaf_groups[leaf_id].append(fpath)
                has_uuid = True
            else:
                fallback_records.append(rec)

        if has_uuid:
            # ---------- 按 leaf_id 分组划分 ----------
            all_leaf_ids = list(leaf_groups.keys())
            random.shuffle(all_leaf_ids)
            n = len(all_leaf_ids)
            n_train = int(n * TRAIN_RATIO)
            n_val = int(n * VAL_RATIO)

            train_leaves = set(all_leaf_ids[:n_train])
            val_leaves = set(all_leaf_ids[n_train:n_train + n_val])

            for leaf_id, fpaths in leaf_groups.items():
                group = "train" if leaf_id in train_leaves else (
                    "val" if leaf_id in val_leaves else "test")
                for fp in fpaths:
                    splits[group].append((fp, label_id))

            n1, n2, n3 = len(all_leaf_ids), n_train, n_val
           
            # 该类若无 fallback 记录则 skip
            if not fallback_records:
                continue

        # ---------- fallback 或只有 fallback ----------
        # 把 fallback 记录按类别内随机划分
        n = len(fallback_records)
        indices = list(range(n))
        random.shuffle(indices)
        n_train = int(n * TRAIN_RATIO)
        n_val = int(n * VAL_RATIO)

        for i in indices[:n_train]:
            splits["train"].append((fallback_records[i][0], label_id))
        for i in indices[n_train:n_train + n_val]:
            splits["val"].append((fallback_records[i][0], label_id))
        for i in indices[n_train + n_val:]:
            splits["test"].append((fallback_records[i][0], label_id))

        if not has_uuid:
            print("  [%s] 无可用 UUID leaf_id，退化为按图片随机划分（%d 张）"
                  % (cn_name, n))

    # 最终打乱每个 split
    for k in splits:
        random.shuffle(splits[k])

    return splits


# ============================================================
# 打印划分统计
# ============================================================
def print_split_stats(splits):
    print("\n" + "=" * 60)
    print("划分结果统计")
    print("=" * 60)
    totals = {}
    for split_name, items in splits.items():
        counter = Counter(lid for _, lid in items)
        print("\n--- %s --- (共 %d 张)" % (split_name, len(items)))
        for lid in range(4):
            count = counter.get(lid, 0)
            cn = LABEL_MAP[str(lid)]["cn"]
            print("  [%d] %-10s: %5d" % (lid, cn, count))
        totals[split_name] = len(items)
    print("\nsplit 总计：train=%d, val=%d, test=%d, 合计=%d"
          % (totals["train"], totals["val"], totals["test"],
             sum(totals.values())))

    expected_total = sum(EXPECTED_COUNTS.values())
    actual_total = sum(totals.values())
    if abs(actual_total - expected_total) > 100:
        print("\n警告：总样本数 %d 与预期 %d 偏差较大，可能原因：" % (actual_total, expected_total))
        print("  - 本地数据集版本与 PPT/文档引用版本不同")
        print("  - 部分文件损坏或格式不支持被跳过")


# ============================================================
# 本地缓存：保存划分结果 + label_map
# ============================================================
def save_cache(splits):
    """将 splits (dict) 序列化为 JSON，保存到 corn_subset/"""
    os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)

    for split_name, items in splits.items():
        cache_file = os.path.join(LOCAL_CACHE_DIR, "%s.json" % split_name)
        data = [{"path": fp, "label": lid} for fp, lid in items]
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("已缓存 %s -> %s (%d 条)" % (split_name, cache_file, len(data)))

    # 额外保存一份 label_map.json 到 data/ 根目录
    os.makedirs(os.path.dirname(LABEL_MAP_PATH), exist_ok=True)
    with open(LABEL_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(LABEL_MAP, f, ensure_ascii=False, indent=2)
    print("label_map 已保存 -> %s" % LABEL_MAP_PATH)


def load_cache():
    """从本地 JSON 缓存加载划分结果"""
    splits = {}
    for split_name in ("train", "val", "test"):
        cache_file = os.path.join(LOCAL_CACHE_DIR, "%s.json" % split_name)
        if not os.path.exists(cache_file):
            raise FileNotFoundError(
                "本地缓存不存在：%s\n请先运行 python data_loader.py 生成缓存"
                % cache_file)
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        splits[split_name] = [(item["path"], item["label"]) for item in data]
        print("已加载 %s -> %d 条" % (split_name, len(splits[split_name])))
    return splits


# ============================================================
# Dataset + DataLoader（WeightedRandomSampler 解决类别不平衡）
# ============================================================
class CornDataset(Dataset):
    """简单 Dataset，从 (fpath, label) 列表读取图片"""

    def __init__(self, items, transform=None):
        self.items = items
        self.transform = transform

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        fpath, label = self.items[idx]
        try:
            img = Image.open(fpath).convert("RGB")
        except Exception as e:
            # 图片损坏则跳过，返回同类别另一个样本
            print("警告：图片损坏，尝试替代 -> %s: %s" % (fpath, e))
            alt_idx = (idx + 1) % len(self.items)
            fpath, label = self.items[alt_idx]
            img = Image.open(fpath).convert("RGB")

        if self.transform is not None:
            img = self.transform(img)
        return img, label


def build_dataloaders(splits, batch_size=32, num_workers=0):
    """
    构建 DataLoader。
    训练集使用 WeightedRandomSampler 做类别均衡，
    val/test 用普通 DataLoader（shuffle=False）。
    """
    transform_train = get_transforms("train")
    transform_eval = get_transforms("val")

    datasets = {
        "train": CornDataset(splits["train"], transform_train),
        "val": CornDataset(splits["val"], transform_eval),
        "test": CornDataset(splits["test"], transform_eval),
    }

    # ---------- 训练集：WeightedRandomSampler ----------
    train_labels = [lid for _, lid in splits["train"]]
    class_counts = Counter(train_labels)
    weights = [1.0 / class_counts[lid] for lid in train_labels]
    sampler = WeightedRandomSampler(
        weights=weights, num_samples=len(train_labels), replacement=True
    )
    print("WeightedRandomSampler 已启用，各训练类样本权重：")
    for lid in range(4):
        print("  [%d] %-10s: count=%d, weight=%.4f"
              % (lid, LABEL_MAP[str(lid)]["cn"],
                 class_counts.get(lid, 0),
                 1.0 / class_counts.get(lid, 1)))

    loaders = {
        "train": DataLoader(
            datasets["train"], batch_size=batch_size, sampler=sampler,
            num_workers=num_workers, pin_memory=True
        ),
        "val": DataLoader(
            datasets["val"], batch_size=batch_size, shuffle=False,
            num_workers=num_workers, pin_memory=True
        ),
        "test": DataLoader(
            datasets["test"], batch_size=batch_size, shuffle=False,
            num_workers=num_workers, pin_memory=True
        ),
    }

    return datasets, loaders


# ============================================================
# main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="玉米病害数据集加载（本地文件夹版）")
    parser.add_argument("--use_local_cache", action="store_true",
                        help="直接加载本地 corn_subset，跳过扫描和划分")
    args = parser.parse_args()

    set_seed(SEED)

    if args.use_local_cache:
        splits = load_cache()
    else:
        print("正在扫描 %s 下的玉米文件夹..." % DATA_ROOT)
        records = scan_corn_images()
        if not records:
            print("错误：未找到任何玉米类图片，请检查路径是否正确")
            return

        print("\n正在按类别划分 train/val/test (7:1.5:1.5, seed=%d)..." % SEED)
        splits = split_by_class(records, seed=SEED)
        print_split_stats(splits)

        print("\n正在保存本地缓存...")
        save_cache(splits)

    # 验证 DataLoader 能正常跑通
    print("\n正在验证 DataLoader 构建...")
    datasets, loaders = build_dataloaders(splits, batch_size=8, num_workers=0)
    for split_name, loader in loaders.items():
        try:
            batch = next(iter(loader))
            print("  %s: batch shape=%s, label sample=%s"
                  % (split_name, tuple(batch[0].shape), batch[1].tolist()[:4]))
        except Exception as e:
            print("  %s: 构建失败 -> %s" % (split_name, e))
            import traceback
            traceback.print_exc()

    print("\n数据加载准备就绪，可以开始训练。")


if __name__ == "__main__":
    main()
