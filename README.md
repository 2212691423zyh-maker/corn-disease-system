# 滦州玉米病害多模态识别与防治系统的设计与实现

> 本项目是一个全栈 AI 落地应用，旨在解决农户“认病难、乱用药”的痛点。系统深度融合了**计算机视觉（图像识别）**与**自然语言处理（RAG 问答）**，实现了一套从视觉模型微调、混合检索、到大模型生成的完整多模态业务闭环。

## 🛠 技术栈
- **前端**: Vue 3 + Vite + Element Plus + ECharts
- **后端**: Python + FastAPI + Uvicorn (异步非阻塞架构)
- **算法与 AI**: PyTorch, ResNet50 (迁移学习), BGE-M3 (向量化), FAISS + BM25 (混合检索), BGE-Reranker (精排), DeepSeek API
- **工程架构**: 多级策略降级 (本地模型 -> 云端 API -> Mock)

## ✨ 核心亮点

1. **高精度本地视觉模型微调**
   - 基于 PlantVillage 玉米数据集，使用 ResNet50 进行两阶段迁移学习微调（Baseline vs Finetune）。
   - 引入 `WeightedRandomSampler` 完美解决类别不平衡问题，最终测试集准确率达到 **95.88%**。
   - 支持纯本地推理，彻底摆脱对云端 API 的强依赖。

2. **企业级 RAG 混合检索与精排架构**
   - 采用 **FAISS 稠密向量 + BM25 稀疏检索** 的双路召回策略，兼顾语义泛化与专有名词的精准命中。
   - 引入 **BGE-Reranker 交叉编码器** 进行二阶段重排，截取 Top-5 上下文，大幅降低无关信息对大模型的干扰。
   - 采用合理的 **Chunking（分块）与 Overlap（重叠）策略**，保障农业长文本与表格的上下文完整性。

3. **抗幻觉（Anti-hallucination）与可解释性**
   - 严格约束 Prompt 与检索上下文边界。若知识库无记载，模型坚决不瞎编，并提示缺失。
   - 问答结果自带 **文献引用溯源** 与置信度分数，确保每一条农业建议都有据可查。

4. **高可用的工程化设计与部署**
   - **多级降级兜底**：图像识别链路遵循 `本地 ResNet50 -> 云端 Qwen-VL -> Mock 引擎` 的降级策略，保障极端断网环境下系统的高可用。
   - **零系统依赖导出**：放弃传统的后端 PDF 生成库，采用前端 `html2canvas` + `jsPDF` 方案，实现“所见即所得”，彻底规避服务器 GTK 依赖痛点。

## 📺 演示视频
👉 **[点击查看 B 站完整演示视频](https://www.bilibili.com/video/BV1dWHP6ZEUx/)**

## 🚀 快速开始

### 1. 启动后端 (FastAPI)
```bash
cd backend
# 安装依赖
pip install -r requirements.txt
# 配置环境变量（请参考 .env.example 新建 .env 并填入你的 DeepSeek API Key）
# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
### 2. 启动前端 (Vue 3)
```bash
cd frontend
# 安装依赖
npm install
# 启动开发服务器
npm run dev
```

*Created by 张云昊 | 2026*