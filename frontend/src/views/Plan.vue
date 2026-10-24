<template>
  <div class="page-container">
    <h2 class="card-title">防治方案生成</h2>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>方案参数</template>
          <el-form label-position="top">
            <el-form-item label="病害名称">
              <el-select v-model="form.disease_name" filterable placeholder="选择或输入病害名称" style="width:100%">
                <el-option
                  v-for="d in diseaseList"
                  :key="d"
                  :label="d"
                  :value="d"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="症状描述（可选）">
              <el-input v-model="form.symptoms" type="textarea" :rows="4" placeholder="描述病灶特征、颜色、位置等" />
            </el-form-item>
            <el-button type="primary" :loading="generating" @click="generate" style="width:100%">
              生成防治方案
            </el-button>
          </el-form>
        </el-card>

        <el-card shadow="hover" style="margin-top: 16px">
          <template #header>快速生成</template>
          <div class="quick-list">
            <el-button
              v-for="q in quickDiseases"
              :key="q"
              size="small"
              round
              @click="generateQuick(q)"
            >{{ q }}</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="14">
        <div v-if="!plan && !generating" class="empty-state">
          <el-icon class="empty-icon"><DocumentChecked /></el-icon>
          <p>选择病害后生成方案，支持导出 Word 文档</p>
        </div>

        <el-card v-else-if="generating" shadow="hover">
          <el-skeleton :rows="8" animated />
        </el-card>

        <div v-else ref="planWrap">
          <el-card shadow="hover">
            <template #header>
              <div class="plan-header">
                <span class="plan-title">{{ plan.plan_title }}</span>
                <div>
                  <el-button size="small" @click="exportWord"><el-icon><Download /></el-icon> Word 导出</el-button>
                  <el-button size="small" type="primary" @click="exportPDF"><el-icon><Printer /></el-icon> PDF 导出</el-button>
                </div>
              </div>
            </template>

            <h4 class="section-h4">💊 用药方案</h4>
            <el-table :data="plan.medication_plan || []" border size="small">
              <el-table-column prop="drug" label="药剂" width="180" />
              <el-table-column prop="dosage" label="剂量" width="160" />
              <el-table-column prop="frequency" label="频率" width="160" />
              <el-table-column prop="precautions" label="注意事项" />
            </el-table>
            <el-empty v-if="!plan.medication_plan?.length" description="暂无用药建议" :image-size="80" />

            <h4 class="section-h4">🌱 施肥方案</h4>
            <div v-for="(f, i) in plan.fertilization_plan" :key="i" class="fert-item">
              <el-tag>{{ f.type }}</el-tag> {{ f.dosage }} · {{ f.timing }}
            </div>

            <h4 class="section-h4">📋 综合防治建议</h4>
            <div class="markdown-body" v-html="renderMd(plan.prevention_tips)"></div>

            <h4 class="section-h4">🌾 农业操作建议</h4>
            <div class="markdown-body" v-html="renderMd(plan.agricultural_operations)"></div>
          </el-card>

          <el-card v-if="plan.rag_evidence?.length" shadow="hover" style="margin-top: 16px">
            <template #header>RAG 知识支撑（{{ plan.model_used }}）</template>
            <el-timeline>
              <el-timeline-item
                v-for="(e, i) in plan.rag_evidence"
                :key="i"
                :timestamp="e.source"
              >
                {{ e.citation }}
                <el-tag size="small" type="success" style="margin-left:8px">置信 {{ e.score }}</el-tag>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentChecked, Download, Printer } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { marked } from 'marked'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'

const form = ref({ disease_name: '', symptoms: '' })
const generating = ref(false)
const plan = ref(null)
const planWrap = ref(null)

const diseaseList = [
  '玉米南方锈病', '玉米大斑病', '玉米小斑病', '玉米纹枯病', '玉米丝黑穗病',
  '玉米黑粉病', '玉米普通锈病', '玉米褐斑病', '玉米霜霉病', '玉米粗缩病',
  '玉米蚜虫', '玉米螟', '玉米粘虫', '玉米红蜘蛛', '玉米蓟马',
  '玉米茎腐病', '玉米穗腐病', '玉米灰斑病', '玉米细菌性茎腐病',
]
const quickDiseases = ['玉米南方锈病', '玉米大斑病', '玉米螟', '玉米蚜虫']

function renderMd(t) { return marked.parse(t || '') }

async function generate() {
  if (!form.value.disease_name) return ElMessage.warning('请选择病害')
  generating.value = true
  plan.value = null
  try {
    const { data } = await request.post('/api/plan/generate', form.value)
    plan.value = data
    ElMessage.success('方案生成完成')
  } catch {
    ElMessage.error('生成失败')
  } finally {
    generating.value = false
  }
}

function generateQuick(name) {
  form.value.disease_name = name
  generate()
}

async function exportWord() {
  if (!plan.value) return
  try {
    const res = await request.post('/api/plan/export/1', plan.value, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `防治方案_${plan.value.plan_title || Date.now()}.docx`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('Word 导出完成')
  } catch {
    ElMessage.error('Word 导出失败')
  }
}

async function exportPDF() {
  if (!planWrap.value) return
  try {
    ElMessage.info('正在生成 PDF...')
    const canvas = await html2canvas(planWrap.value, { scale: 2, useCORS: true })
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pw = pdf.internal.pageSize.getWidth()
    const ph = pdf.internal.pageSize.getHeight()
    const iw = pw - 20
    const ih = canvas.height * iw / canvas.width
    let hl = ih, pos = 10
    pdf.addImage(imgData, 'PNG', 10, pos, iw, ih)
    hl -= ph
    while (hl > 0) {
      pos = hl - ih + 10
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 10, pos, iw, ih)
      hl -= ph
    }
    pdf.save(`防治方案_${Date.now()}.pdf`)
    ElMessage.success('PDF 已下载')
  } catch (e) {
    ElMessage.error('PDF 生成失败: ' + e.message)
  }
}
</script>

<style scoped>
.empty-state { text-align: center; padding: 80px 0; color: #c0c4cc; }
.empty-icon { font-size: 64px; }
.plan-header { display: flex; justify-content: space-between; align-items: center; }
.plan-title { font-size: 17px; font-weight: 600; color: #303133; }
.section-h4 { margin: 18px 0 10px; color: #1e3a2f; font-size: 15px; border-left: 4px solid #67c23a; padding-left: 8px; }
.fert-item { margin-bottom: 6px; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 20px; line-height: 1.8; }
.quick-list { display: flex; flex-wrap: wrap; gap: 6px; }
</style>
