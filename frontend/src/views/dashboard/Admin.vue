<template>
  <div class="dashboard">
    <!-- 欢迎横幅 -->
    <div class="hero">
      <div class="hero-left">
        <div class="hero-title">{{ greeting }}，{{ userStore.nickname || userStore.username }}</div>
        <div class="hero-sub">超级管理员控制台 · 平台健康度 {{ healthScore }}%，今日新增检测 {{ todayCount }} 次</div>
        <div class="hero-tags">
          <el-tag type="info" effect="dark">用户 {{ overview.userCount || 0 }}</el-tag>
          <el-tag type="warning" effect="dark">隔离 {{ overview.quarantineCount || 0 }}</el-tag>
          <el-tag type="danger" effect="dark">待处理告警 {{ overview.alertCount || 0 }}</el-tag>
        </div>
      </div>
      <div class="hero-right">
        <el-icon :size="64"><Monitor /></el-icon>
      </div>
    </div>

    <!-- 顶部统计卡片 -->
    <div class="stat-row">
      <div class="stat-card" v-for="(s, i) in stats" :key="i">
        <div class="stat-icon" :style="{ background: s.bg }"><el-icon :size="22"><component :is="s.icon" /></el-icon></div>
        <div class="stat-info">
          <div class="stat-label">{{ s.label }}</div>
          <div class="stat-value">{{ s.value }}</div>
        </div>
      </div>
    </div>

    <!-- 第一行：检测趋势 + 风险等级 -->
    <div class="chart-row">
      <div class="chart-card big">
        <div class="chart-title">近30天检测趋势</div>
        <div ref="trendRef" class="chart-body"></div>
      </div>
      <div class="chart-card small">
        <div class="chart-title">风险等级分布</div>
        <div ref="riskRef" class="chart-body"></div>
      </div>
    </div>

    <!-- 第二行：4 个 mini 图 -->
    <div class="chart-row">
      <div class="chart-card mini">
        <div class="chart-title">语言分布</div>
        <div ref="langRef" class="chart-body"></div>
      </div>
      <div class="chart-card mini">
        <div class="chart-title">检测类型</div>
        <div ref="typeRef" class="chart-body"></div>
      </div>
      <div class="chart-card mini">
        <div class="chart-title">告警状态</div>
        <div ref="alertRef" class="chart-body"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi } from '@/api'
import { useUserStore } from '@/store/user'
import { Document, Warning, Files, View, Monitor } from '@element-plus/icons-vue'

const userStore = useUserStore()
const overview = reactive({})
const stats = ref([
  { label: '检测任务', value: 0, icon: 'Document', bg: '#1a3a5f' },
  { label: '发现Webshell', value: 0, icon: 'Warning', bg: '#f56c6c' },
  { label: '隔离文件', value: 0, icon: 'Files', bg: '#e6a23c' },
  { label: '待处理告警', value: 0, icon: 'View', bg: '#67c23a' }
])
const todayCount = ref(0)
const healthScore = computed(() => {
  const a = overview.alertCount || 0
  return Math.max(60, 100 - a * 3)
})
const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const trendRef = ref(), riskRef = ref(), langRef = ref(), typeRef = ref(), alertRef = ref()
let charts = []
function makeChart(el, opt) { const c = echarts.init(el); c.setOption(opt); charts.push(c); return c }
const colorPalette = ['#1a3a5f', '#2c5282', '#2d8cf0', '#5dade2', '#85c1e9', '#aed6f1']

async function load() {
  const ov = await dashboardApi.overview()
  Object.assign(overview, ov.data)
  stats.value[0].value = ov.data.totalTasks
  stats.value[1].value = ov.data.webshellCount
  stats.value[2].value = ov.data.quarantineCount
  stats.value[3].value = ov.data.alertCount
  await nextTick()

  const trend = await dashboardApi.trend()
  todayCount.value = trend.data.counts[trend.data.counts.length - 1] || 0
  makeChart(trendRef.value, {
    grid: { top: 30, right: 20, bottom: 30, left: 40 },
    tooltip: { trigger: 'axis' },
    legend: { data: ['检测任务'], right: 10, top: 0, textStyle: { fontSize: 11 } },
    xAxis: { type: 'category', data: trend.data.dates, axisLabel: { fontSize: 9, interval: 4 } },
    yAxis: { type: 'value' },
    series: [{ name: '检测任务', type: 'line', data: trend.data.counts, smooth: true,
      itemStyle: { color: '#1a3a5f' }, areaStyle: { color: 'rgba(26,58,95,0.15)' } }]
  })

  const risk = await dashboardApi.riskLevel()
  makeChart(riskRef.value, {
    tooltip: { trigger: 'item' },
    color: ['#f56c6c', '#e6a23c', '#909399', '#67c23a'],
    series: [{ type: 'pie', radius: ['45%', '70%'], label: { fontSize: 11 },
      data: risk.data.levels.map((lv, i) => ({ name: lv, value: risk.data.counts[i] })) }]
  })

  const lang = await dashboardApi.langDist()
  makeChart(langRef.value, { tooltip: { trigger: 'item' }, color: colorPalette,
    series: [{ type: 'pie', radius: '70%', label: { fontSize: 10 }, data: lang.data }] })

  const type = await dashboardApi.detectType()
  makeChart(typeRef.value, {
    grid: { top: 20, right: 10, bottom: 30, left: 40 }, tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: type.data.map(d => d.name), axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: type.data.map(d => d.value), itemStyle: { color: '#2c5282' }, barWidth: '50%' }]
  })

  const al = await dashboardApi.alertStatus()
  makeChart(alertRef.value, { tooltip: { trigger: 'item' },
    color: ['#f56c6c', '#e6a23c', '#67c23a', '#909399'],
    series: [{ type: 'pie', radius: ['40%', '70%'], label: { fontSize: 10 }, data: al.data }] })
}

function onResize() { charts.forEach(c => c.resize()) }
onMounted(() => { load(); window.addEventListener('resize', onResize) })
onBeforeUnmount(() => { window.removeEventListener('resize', onResize); charts.forEach(c => c.dispose()) })
</script>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 12px; height: 100%; }

.hero {
  background: linear-gradient(135deg, #1a3a5f 0%, #2c5282 100%);
  color: #fff; border-radius: 8px; padding: 18px 24px;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 2px 12px rgba(26,58,95,0.2);
}
.hero-title { font-size: 20px; font-weight: 600; margin-bottom: 6px; }
.hero-sub { font-size: 13px; opacity: 0.85; margin-bottom: 10px; }
.hero-tags { display: flex; gap: 8px; }
.hero-right { opacity: 0.6; }

.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.stat-card { background: #fff; border-radius: 6px; padding: 14px 16px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.stat-icon { width: 44px; height: 44px; border-radius: 8px; color: #fff; display: flex; align-items: center; justify-content: center; }
.stat-label { font-size: 12px; color: #909399; }
.stat-value { font-size: 22px; font-weight: 600; color: #1a3a5f; margin-top: 2px; }

.chart-row { display: flex; gap: 12px; flex: 1; min-height: 0; }
.chart-card { background: #fff; border-radius: 6px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); display: flex; flex-direction: column; }
.chart-card.big { flex: 2; min-height: 0; }
.chart-card.small { flex: 1; min-height: 0; }
.chart-card.mini { flex: 1; min-height: 0; }
.chart-title { font-size: 14px; font-weight: 600; color: #1a3a5f; margin-bottom: 8px; }
.chart-body { flex: 1; min-height: 180px; }
</style>
