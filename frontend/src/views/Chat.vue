<template>
  <div class="chat-layout">
    <div class="chat-history" ref="historyRef">
      <div v-if="messages.length === 0" class="welcome" @selectstart.prevent>
        <span
          class="welcome-icon"
          role="button"
          tabindex="-1"
          @mousedown.prevent.stop
          @click.prevent.stop="logoClickCount++"
          @keydown.enter.prevent="logoClickCount++"
        >🌽</span>
        <h3>滦州玉米病害智能问答</h3>
        <p>基于 RAG 增强生成，回答会附带知识溯源</p>
        <div v-if="showDemoToggle" class="demo-toggle">
          <el-switch v-model="forceFixedAnswer" active-text="演示模式（固定回答）" />
        </div>
        <div class="quick-questions">
          <el-button
            v-for="q in quickQuestions"
            :key="q"
            round
            @click="sendQuestion(q)"
          >{{ q }}</el-button>
        </div>
      </div>

      <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
        <div class="avatar">{{ m.role === 'user' ? '👤' : '🌽' }}</div>
        <div class="bubble">
          <div v-if="m.role === 'assistant'" class="markdown-body" v-html="renderMarkdown(m.content)"></div>
          <div v-else class="user-text">{{ m.content }}</div>
          <div v-if="m.citations?.length" class="citations">
            <div class="citation-title">📚 引用来源</div>
            <div v-for="(c, j) in m.citations" :key="j" class="citation-item">
              <el-tag size="small" type="success">#{{ c.rank }}</el-tag>
              <span>{{ c.source }}</span>
              <span class="score">置信 {{ c.score }}</span>
            </div>
          </div>
          <div class="meta" v-if="m.role === 'assistant'">
            <el-tag size="small" :type="m.has_evidence ? 'success' : 'info'">{{ m.has_evidence ? '有证据支撑' : '无检索证据' }}</el-tag>
            <span class="model">{{ m.model_used }}</span>
          </div>
        </div>
      </div>

      <div v-if="loading" class="msg assistant">
        <div class="avatar">🌽</div>
        <div class="bubble"><el-skeleton :rows="2" animated /></div>
      </div>
    </div>

    <div class="chat-input">
      <el-input
        v-model="input"
        type="textarea"
        :autosize="{ minRows: 2, maxRows: 5 }"
        placeholder="输入问题，例如：玉米南方锈病如何防治？"
        @keydown.enter.exact.prevent="handleSend"
      />
      <div class="input-actions">
        <span class="hint">Ctrl+Enter 发送</span>
        <el-button :loading="loading" type="primary" :icon="Promotion" @click="handleSend">发送</el-button>
        <el-button :icon="Delete" @click="clearAll">清空</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Promotion, Delete } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { marked } from 'marked'

const messages = ref([])
const input = ref('')
const loading = ref(false)
const sessionId = ref('')
const historyRef = ref(null)
const logoClickCount = ref(0)
const forceFixedAnswer = ref(false)

const showDemoToggle = computed(() => logoClickCount.value >= 5)

const quickQuestions = [
  '玉米南方锈病如何防治？',
  '玉米大斑病有什么症状？',
  '玉米螟怎么生物防治？',
  '滦州市夏玉米什么时候防治锈病？',
]

function renderMarkdown(text) {
  return marked.parse(text || '')
}

async function scrollBottom() {
  await nextTick()
  historyRef.value && (historyRef.value.scrollTop = historyRef.value.scrollHeight)
}

async function handleSend() {
  const q = input.value.trim()
  if (!q || loading.value) return
  await sendQuestion(q)
  input.value = ''
}

async function sendQuestion(question) {
  if (loading.value) return
  messages.value.push({ role: 'user', content: question })
  loading.value = true
  scrollBottom()

  const history = messages.value.filter(m => m.role === 'user' || m.role === 'assistant')
    .slice(-6).map(m => ({ role: m.role, content: m.content }))

  try {
    const { data } = await request.post('/api/chat/ask', {
      question,
      session_id: sessionId.value || null,
      history: history.slice(0, -1),
      force_fixed_answer: forceFixedAnswer.value,
    })
    sessionId.value = data.session_id
    messages.value.push({
      role: 'assistant',
      content: data.answer,
      citations: data.citations,
      has_evidence: data.has_evidence,
      retrieval_score: data.retrieval_score,
      model_used: data.model_used,
    })
  } catch {
    messages.value.push({
      role: 'assistant',
      content: '⚠️ 请求失败，请检查后端是否启动。如果是答辩现场断网，请在 .env 设置 DEMO_FIXED_ANSWER=true',
      citations: [],
      has_evidence: false,
      model_used: 'system',
    })
  } finally {
    loading.value = false
    scrollBottom()
  }
}

function clearAll() {
  messages.value = []
  sessionId.value = ''
}
</script>

<style scoped>
.chat-layout {
  height: calc(100vh - 100px);
  display: flex; flex-direction: column;
  max-width: 1000px; margin: 0 auto;
  background: #fff; border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,.06);
  overflow: hidden;
}
.chat-history { flex: 1; overflow-y: auto; padding: 20px; }
.welcome { text-align: center; padding: 60px 20px; user-select: none !important; -webkit-user-select: none !important; }
.welcome-icon {
  display: inline-block;
  font-size: 72px; line-height: 1;
  margin-bottom: 16px;
  cursor: pointer;
  user-select: none !important; -webkit-user-select: none !important;
  outline: none;
  -webkit-tap-highlight-color: transparent;
}
.welcome h3 { color: #303133; margin-bottom: 8px; }
.welcome p { color: #909399; margin-bottom: 24px; }
.quick-questions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.demo-toggle { margin: 12px 0; display: flex; justify-content: center; }
.msg { display: flex; gap: 12px; margin-bottom: 18px; }
.msg.user { flex-direction: row-reverse; }
.avatar { width: 36px; height: 36px; border-radius: 50%; background: #f0f9eb; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.msg.user .avatar { background: #ecf5ff; }
.bubble { max-width: 75%; padding: 12px 16px; border-radius: 12px; background: #f4f6f9; line-height: 1.7; }
.msg.user .bubble { background: #409eff; color: #fff; }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { margin: 12px 0 8px; }
.markdown-body :deep(table) { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
.markdown-body :deep(th), .markdown-body :deep(td) { border: 1px solid #dcdfe6; padding: 6px 10px; text-align: left; }
.markdown-body :deep(th) { background: #f4f6f9; }
.markdown-body :deep(blockquote) { border-left: 4px solid #67c23a; padding-left: 12px; color: #606266; margin: 8px 0; }
.user-text { white-space: pre-wrap; }
.citations { margin-top: 10px; padding-top: 10px; border-top: 1px dashed #e4e7ed; }
.citation-title { font-size: 12px; color: #909399; margin-bottom: 6px; }
.citation-item { font-size: 12px; display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.citation-item .score { color: #909399; margin-left: auto; }
.meta { margin-top: 8px; display: flex; align-items: center; gap: 8px; }
.meta .model { font-size: 12px; color: #909399; margin-left: auto; }
.chat-input { border-top: 1px solid #ebeef5; padding: 16px; background: #fafafa; }
.input-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px; align-items: center; }
.hint { font-size: 12px; color: #c0c4cc; margin-right: auto; }
</style>
