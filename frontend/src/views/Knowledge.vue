<template>
  <div class="page-container">
    <h2 class="card-title">知识库管理</h2>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>上传文档</template>
          <el-upload
            drag
            action="/api/knowledge/upload"
            :auto-upload="true"
            :show-file-list="false"
            :on-success="handleSuccess"
            :on-error="handleError"
            accept=".pdf,.doc,.docx,.txt"
          >
            <el-icon class="el-icon--upload upload-icon"><upload-filled /></el-icon>
            <div class="el-upload__text">拖拽或 <em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 PDF / Word / TXT，最大 50MB</div>
            </template>
          </el-upload>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div class="stats-header">
              <span>索引状态</span>
              <el-tag :type="stats.retrieval_ready ? 'success' : 'warning'">
                {{ stats.retrieval_ready ? '就绪' : '空索引' }}
              </el-tag>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="已索引文档">{{ stats.total_documents }}</el-descriptions-item>
            <el-descriptions-item label="分块总数">{{ stats.total_chunks }}</el-descriptions-item>
            <el-descriptions-item label="向量索引">
              <el-tag :type="stats.index_present ? 'success' : 'info'" size="small">
                {{ stats.index_present ? '✅ 已建立' : '空' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="BM25 索引">
              <el-tag :type="stats.bm25_present ? 'success' : 'info'" size="small">
                {{ stats.bm25_present ? '✅ 已建立' : '空' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="hover" style="margin-top: 16px">
          <template #header>索引详情</template>
          <pre class="engine-info">{{ JSON.stringify(stats.engine_config, null, 2) }}</pre>
          <el-alert v-if="stats.note" :title="stats.note" type="info" show-icon :closable="false" style="margin-top:12px" />
        </el-card>
        <el-card shadow="hover" style="margin-top: 16px">
          <template #header>
            <div class="stats-header">
              <span>文档列表</span>
              <el-button size="small" :icon="Refresh" @click="loadDocs">刷新</el-button>
            </div>
          </template>
          <el-table :data="documents" stripe v-loading="docsLoading" empty-text="暂无文档，请上传">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="filename" label="文件名" min-width="180" show-overflow-tooltip />
            <el-table-column prop="doc_type" label="类型" width="90">
              <template #default="{ row }">
                <el-tag size="small">{{ row.doc_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="chunk_count" label="分块数" width="90" />
            <el-table-column prop="file_size" label="大小" width="110">
              <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status === 'indexed' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button size="small" type="danger" link @click="removeDoc(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Refresh } from '@element-plus/icons-vue'
import request from '@/utils/request'

const stats = ref({
  total_documents: 0,
  total_chunks: 0,
  retrieval_ready: false,
  index_present: false,
  bm25_present: false,
  engine_config: {},
})
const documents = ref([])
const docsLoading = ref(false)

async function loadStats() {
  try {
    const { data } = await request.get('/api/stats/overview')
    stats.value = { ...stats.value, ...data }
  } catch {}
}

async function loadDocs() {
  docsLoading.value = true
  try {
    const { data } = await request.get('/api/knowledge/documents')
    documents.value = data.documents || []
  } catch {}
  finally {
    docsLoading.value = false
  }
}

async function removeDoc(id) {
  try {
    await ElMessageBox.confirm('确定删除该文档？相关索引分块也会一并删除。', '确认', { type: 'warning' })
  } catch {
    return
  }
  try {
    await request.delete(`/api/knowledge/documents/${id}`)
    ElMessage.success('删除成功')
    loadDocs()
    loadStats()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

function handleSuccess(response) {
  if (response.status === 'indexed') {
    ElMessage.success(`索引完成！分块数: ${response.chunk_count}`)
  } else if (response.status === 'failed') {
    ElMessage.error('索引失败: ' + (response.error || '未知错误'))
  } else {
    ElMessage.info('上传成功')
  }
  loadStats()
  loadDocs()
}

function handleError(err) {
  ElMessage.error('上传失败: ' + (err?.response?.data?.detail || err.message))
}

onMounted(() => {
  loadStats()
  loadDocs()
})
</script>

<style scoped>
.upload-icon { font-size: 48px; color: #67c23a; margin-bottom: 12px; }
.stats-header { display: flex; justify-content: space-between; align-items: center; }
.engine-info { background: #f5f7fa; padding: 12px; border-radius: 4px; font-size: 12px; overflow: auto; }
</style>
