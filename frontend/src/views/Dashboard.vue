<template>
  <div class="page-container">
    <h2 class="card-title">数据统计看板</h2>

    <el-row :gutter="16" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background:#e1f3d8;color:#67c23a">📚</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_documents || 0 }}</div>
            <div class="stat-label">知识库文档</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background:#ecf5ff;color:#409eff">🧩</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_chunks || 0 }}</div>
            <div class="stat-label">知识分块</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background:#fdf6ec;color:#e6a23c">🔍</div>
          <div class="stat-info">
            <div class="stat-value">{{ mockData.recognitions }}</div>
            <div class="stat-label">识别次数（示例）</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background:#fef0f0;color:#f56c6c">💬</div>
          <div class="stat-info">
            <div class="stat-value">{{ mockData.chats }}</div>
            <div class="stat-label">RAG 问答（示例）</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>疑似病害对比（柱状图）</template>
          <div ref="barChartRef" style="height:340px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>病害占比分布（饼图）</template>
          <div ref="pieChartRef" style="height:340px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>周度识别趋势（折线图）</template>
          <div ref="lineChartRef" style="height:300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import request from '@/utils/request'

const stats = ref({})
const barChartRef = ref(null)
const pieChartRef = ref(null)
const lineChartRef = ref(null)
let barChart, pieChart, lineChart

const mockData = {
  recognitions: 128,
  chats: 356,
  diseases: [
    { name: '玉米南方锈病', count: 42, pct: 32.8 },
    { name: '玉米大斑病', count: 28, pct: 21.9 },
    { name: '玉米小斑病', count: 18, pct: 14.1 },
    { name: '玉米纹枯病', count: 14, pct: 10.9 },
    { name: '玉米蚜虫', count: 12, pct: 9.4 },
    { name: '玉米螟', count: 9, pct: 7.0 },
    { name: '其他', count: 5, pct: 3.9 },
  ],
}

async function loadStats() {
  try {
    const { data } = await request.get('/api/stats/overview')
    stats.value = data
  } catch {}
}

function initBarChart() {
  barChart = echarts.init(barChartRef.value)
  barChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: mockData.diseases.map(d => d.name),
      axisLabel: { rotate: 25, fontSize: 11 },
    },
    yAxis: { type: 'value', name: '识别次数' },
    series: [{
      type: 'bar',
      data: mockData.diseases.map(d => d.count),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#67c23a' },
          { offset: 1, color: '#1e3a2f' },
        ]),
        borderRadius: [4, 4, 0, 0],
      },
      barWidth: '50%',
    }],
  })
}

function initPieChart() {
  pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}次 ({d}%)' },
    legend: { orient: 'vertical', left: 'left' },
    series: [{
      name: '病害占比',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%' },
      data: mockData.diseases.map(d => ({ name: d.name, value: d.count })),
      color: ['#67c23a', '#409eff', '#e6a23c', '#f56c6c', '#909399', '#8e44ad', '#1abc9c'],
    }],
  })
}

function initLineChart() {
  lineChart = echarts.init(lineChartRef.value)
  lineChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['病害识别', 'RAG 问答'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '病害识别',
        type: 'line',
        smooth: true,
        data: [12, 18, 15, 22, 28, 35, 32],
        itemStyle: { color: '#67c23a' },
        areaStyle: { color: 'rgba(103,194,58,0.15)' },
      },
      {
        name: 'RAG 问答',
        type: 'line',
        smooth: true,
        data: [28, 35, 42, 38, 50, 62, 55],
        itemStyle: { color: '#409eff' },
        areaStyle: { color: 'rgba(64,158,255,0.15)' },
      },
    ],
  })
}

function handleResize() {
  barChart?.resize()
  pieChart?.resize()
  lineChart?.resize()
}

onMounted(async () => {
  await loadStats()
  await nextTick()
  initBarChart()
  initPieChart()
  initLineChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  barChart?.dispose()
  pieChart?.dispose()
  lineChart?.dispose()
})
</script>

<style scoped>
.stat-card { display: flex; align-items: center; gap: 16px; }
.stat-icon {
  width: 52px; height: 52px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 26px; flex-shrink: 0;
}
.stat-value { font-size: 24px; font-weight: 700; color: #303133; }
.stat-label { font-size: 13px; color: #909399; margin-top: 2px; }
</style>
