<template>
  <el-container class="app-layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <span class="logo-icon">🌽</span>
        <span class="logo-text">玉米智能顾问</span>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#1e3a2f"
        text-color="#c8e6d6"
        active-text-color="#67c23a"
      >
        <el-menu-item index="/recognition">
          <el-icon><Camera /></el-icon>
          <span>病害识别</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>RAG 问答</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Reading /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item index="/plan">
          <el-icon><DocumentChecked /></el-icon>
          <span>防治方案</span>
        </el-menu-item>
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据看板</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <h2>{{ currentTitle }}</h2>
        </div>
        <div class="header-right">
          <el-tag v-if="health.force_demo_mode" type="warning" effect="dark">演示模式</el-tag>
          <el-tag v-else-if="health.demo_fixed_answer" type="danger" effect="dark">固定回答安全网</el-tag>
          <el-tag v-else-if="health.deepseek_configured" type="success">DeepSeek 云端</el-tag>
          <el-tag v-else type="info">本地 Mock</el-tag>
          <span class="status-dot" :class="health.ok ? 'ok' : 'err'"></span>
          <span class="status-text">{{ health.ok ? '服务正常' : '离线模式' }}</span>
        </div>
      </el-header>
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { Camera, ChatDotRound, Reading, DocumentChecked, DataAnalysis } from '@element-plus/icons-vue'
import axios from 'axios'

const route = useRoute()
const health = ref({ ok: true, force_demo_mode: false, demo_fixed_answer: false, deepseek_configured: false })

const titleMap = {
  '/recognition': '病害智能识别',
  '/chat': 'RAG 智能问答',
  '/knowledge': '知识库管理',
  '/plan': '防治方案生成',
  '/dashboard': '数据统计看板',
}
const currentTitle = computed(() => titleMap[route.path] || '系统首页')

async function checkHealth() {
  try {
    const { data } = await axios.get('/api/health', { timeout: 3000 })
    health.value = { ok: true, ...data }
  } catch {
    health.value.ok = false
  }
}

let timer
onMounted(() => { checkHealth(); timer = setInterval(checkHealth, 30000) })
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.app-layout { height: 100vh; }
.sidebar { background: #1e3a2f; padding-top: 0; }
.logo {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  height: 60px; background: #153025; color: #fff; font-size: 16px; font-weight: 600;
}
.logo-icon { font-size: 24px; }
:deep(.el-menu) { border-right: none; }
.header {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; border-bottom: 1px solid #ebeef5;
}
.header h2 { margin: 0; font-size: 18px; color: #303133; }
.header-right { display: flex; align-items: center; gap: 12px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.status-dot.ok { background: #67c23a; }
.status-dot.err { background: #f56c6c; }
.status-text { font-size: 13px; color: #909399; }
.main { background: #f4f6f9; overflow-y: auto; }
.fade-enter-active, .fade-leave-active { transition: opacity .2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
