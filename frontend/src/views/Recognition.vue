<template>
  <div class="page-container">
    <h2 class="card-title">病害智能识别</h2>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="upload-card" shadow="hover">
          <div class="upload-area" @click="triggerUpload" @dragover.prevent @drop.prevent="handleDrop">
            <input ref="fileInput" type="file" accept="image/*" hidden @change="handleFile" />
            <div v-if="!imageUrl" class="upload-placeholder">
              <el-icon class="big-icon"><UploadFilled /></el-icon>
              <p>点击或拖拽上传玉米叶片/植株图片</p>
              <p class="tip">支持 JPG / PNG / WEBP，最大 10MB</p>
            </div>
            <img v-else :src="imageUrl" class="preview" />
          </div>
          <div class="upload-actions" v-if="imageUrl">
            <el-button @click="resetImage">重新选择</el-button>
            <el-button type="primary" :loading="recognizing" @click="doRecognize">开始识别</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="14">
        <div v-if="!result && !recognizing" class="empty-state">
          <el-icon class="empty-icon"><Picture /></el-icon>
          <p>上传图片后点击「开始识别」</p>
        </div>
        <el-card v-else-if="recognizing" shadow="hover">
          <el-skeleton :rows="6" animated />
        </el-card>

        <div v-else class="result-wrapper" ref="resultWrap">
          <el-card shadow="hover">
            <template #header>
              <div class="result-header">
                <span>识别结果</span>
                <div>
                  <el-button size="small" @click="exportPDF"><el-icon><Download /></el-icon> 导出报告 (PDF)</el-button>
                </div>
              </div>
            </template>
            <div class="primary-result">
              <div class="disease-name">
                <el-tag type="danger" effect="dark" size="large">{{ result.primary?.name }}</el-tag>
                <el-tag
                  :type="engineTag.type"
                  effect="light"
                  size="large"
                  class="engine-tag"
                >{{ engineTag.text }}</el-tag>
                <el-progress
                  :percentage="Math.round((result.primary?.confidence || 0) * 100)"
                  :stroke-width="14"
                  :color="confidenceColor"
                  style="width: 200px; margin-left: 16px"
                />
                <span class="conf-text">置信度</span>
              </div>
              <div class="detail-section">
                <h4>症状描述</h4>
                <p>{{ result.primary?.symptoms || result.symptoms || '—' }}</p>
              </div>
              <div class="detail-section">
                <h4>发病原因</h4>
                <p>{{ result.primary?.causes || '高温高湿条件下真菌侵染' }}</p>
              </div>
            </div>
          </el-card>

          <el-card shadow="hover" style="margin-top: 16px" v-if="result.rag_evidence?.length">
            <template #header><span>RAG 知识支撑</span></template>
            <el-timeline>
              <el-timeline-item
                v-for="(ev, idx) in result.rag_evidence"
                :key="idx"
                :timestamp="ev.source"
                placement="top"
              >
                <div style="font-size:13px;color:#606266">{{ ev.text }}</div>
                <el-tag size="small" type="success" style="margin-top:6px">置信度 {{ ev.score }}</el-tag>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Picture, Download } from '@element-plus/icons-vue'
import request from '@/utils/request'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'

const fileInput = ref(null)
const imageUrl = ref('')
const imageBytes = ref(null)
const recognizing = ref(false)
const result = ref(null)
const resultWrap = ref(null)

const confidenceColor = computed(() => {
  const c = result.value?.primary?.confidence || 0
  if (c >= 0.8) return '#67c23a'
  if (c >= 0.6) return '#e6a23c'
  return '#f56c6c'
})

const engineTag = computed(() => {
  const engine = result.value?.engine || result.value?.model_used
  if (engine === 'Local_ResNet50') {
    return { type: 'success', text: '🟢 本地模型 (ResNet50)' }
  }
  if (engine === 'Qwen-VL') {
    return { type: 'primary', text: '☁️ 云端模型 (Qwen-VL)' }
  }
  return { type: 'info', text: '⚙️ 演示模式 (Mock)' }
})

function triggerUpload() { fileInput.value?.click() }

function handleFile(e) {
  const f = e.target.files?.[0]
  if (f) loadFile(f)
}

function handleDrop(e) {
  const f = e.dataTransfer.files?.[0]
  if (f && f.type.startsWith('image/')) loadFile(f)
}

function loadFile(f) {
  if (f.size > 10 * 1024 * 1024) return ElMessage.error('图片不能超过 10MB')
  const reader = new FileReader()
  reader.onload = () => {
    imageUrl.value = reader.result
    imageBytes.value = f
  }
  reader.readAsDataURL(f)
}

function resetImage() { imageUrl.value = ''; imageBytes.value = null; result.value = null }

async function doRecognize() {
  if (!imageBytes.value) return
  recognizing.value = true
  result.value = null
  const fd = new FormData()
  fd.append('file', imageBytes.value)
  try {
    const { data } = await request.post('/api/recognition/identify', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    result.value = data
    ElMessage.success('识别完成')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '识别失败')
  } finally {
    recognizing.value = false
  }
}

async function exportPDF() {
  if (!resultWrap.value) return
  try {
    ElMessage.info('正在生成 PDF...')
    const canvas = await html2canvas(resultWrap.value, { scale: 2, useCORS: true })
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const imgWidth = pageWidth - 20
    const imgHeight = canvas.height * imgWidth / canvas.width
    let heightLeft = imgHeight
    let position = 10
    pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight)
    heightLeft -= pageHeight
    while (heightLeft > 0) {
      position = heightLeft - imgHeight + 10
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight)
      heightLeft -= pageHeight
    }
    pdf.save(`病害识别报告_${Date.now()}.pdf`)
    ElMessage.success('PDF 已下载')
  } catch (e) {
    ElMessage.error('PDF 生成失败: ' + e.message)
  }
}
</script>

<style scoped>
.upload-card { text-align: center; }
.upload-area {
  width: 100%; height: 320px; border: 2px dashed #dcdfe6; border-radius: 8px;
  cursor: pointer; transition: all .2s; overflow: hidden;
  display: flex; align-items: center; justify-content: center;
}
.upload-area:hover { border-color: #67c23a; background: #f0f9eb; }
.upload-placeholder { color: #909399; }
.big-icon { font-size: 48px; color: #c0c4cc; margin-bottom: 12px; }
.tip { font-size: 12px; color: #c0c4cc; margin-top: 6px; }
.preview { max-width: 100%; max-height: 310px; object-fit: contain; }
.upload-actions { margin-top: 12px; display: flex; gap: 12px; justify-content: center; }
.empty-state { text-align: center; padding: 80px 0; color: #c0c4cc; }
.empty-icon { font-size: 64px; }
.result-header { display: flex; justify-content: space-between; align-items: center; }
.primary-result .disease-name {
  display: flex; align-items: center; margin-bottom: 20px;
}
.engine-tag { margin-left: 10px; font-size: 14px; }
.conf-text { color: #909399; font-size: 13px; margin-left: 8px; }
.detail-section h4 { color: #67c23a; margin: 14px 0 6px; font-size: 15px; }
.detail-section p { color: #606266; line-height: 1.7; }
</style>
