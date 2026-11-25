<template>
  <div class="dashboard">
    <!-- 安全管理员欢迎横幅 -->
    <div class="hero">
      <div class="hero-left">
        <div class="hero-title">{{ greeting }}，安全管理员 {{ userStore.nickname || userStore.username }}</div>
        <div class="hero-sub">
          当前待处理告警 <b style="color:#fde47f">{{ overview.alertCount || 0 }}</b> 条 ·
          高危隔离 <b style="color:#fde47f">{{ overview.quarantineCount || 0 }}</b> 个 ·
          请优先处理高危告警，确保系统安全
        </div>
        <div class="hero-tags">
          <el-button type="warning" size="small" @click="$router.push('/alert/list')">前往告警中心</el-button>
          <el-button type="info" size="small" @click="$router.push('/detection/quarantine')">隔离区管理</el-button>
        </div>
      </div>
      <div class="hero-right"><el-icon :size="64"><Lock /></el-icon></div>
    </div>

    <!-- 4 个数据卡片 -->
    <div class="stat-row">
      <div class="stat-card">
        <div class="stat-icon" style="background:#f56c6c"><el-icon :size="22"><Warning /></el-icon></div>
        <div class="stat-info"><div class="stat-label">待处理告警</div><div class="stat-value">{{ overview.alertCount || 0 }}</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#e6a23c"><el-icon :size="22"><Files /></el-icon></div>
        <div class="stat-info"><div class="stat-label">隔离文件</div><div class="stat-value">{{ overview.quarantineCount || 0 }}</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#1a3a5f"><el-icon :size="22"><Document /></el-icon></div>
        <div class="stat-info"><div class="stat-label">检测任务</div><div class="stat-value">{{ overview.totalTasks || 0 }}</div></div>
      </div>
    </div>

    <!-- 主体：左趋势 + 右待办告警列表 -->
    <div class="chart-row">
      <div class="chart-card big">
        <div class="chart-title">近30天检测趋势</div>
        <div ref="trendRef" class="chart-body"></div>
      </div>
      <div class="chart-card small list-card">
        <div class="chart-title">实时告警 <el-tag size="small" type="danger" effect="plain">{{ alerts.length }}</el-tag></div>
        <div class="list-body">
          <div v-if="!alerts.length" class="empty">暂无告警</div>
          <div v-for="a in alerts" :key="a.id" class="alert-item" @click="$router.push('/alert/list')">
            <el-tag :type="severityType(a.severity)" size="small" effect="dark" style="flex-shrink:0">{{ severityText(a.severity) }}</el-tag>
            <div class="alert-info">
              <div class="alert-title">{{ a.title }}</div>
              <div class="alert-time">{{ $date(a.create_time) }}</div>
            </div>
            <el-tag size="small" :type="a.status === 'pending' ? 'warning' : 'success'">{{ statusText(a.status) }}</el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部：风险等级 + 告警状态 -->
    <div class="chart-row">
      <div class="chart-card mini">
        <div class="chart-title">风险等级分布</div>
        <div ref="riskRef" class="chart-body"></div>
      </div>
      <div class="chart-card mini">
        <div class="chart-title">告警处理状态</div>
        <div ref="alertChartRef" class="chart-body"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi } from '@/api'
import { useUserStore } from '@/store/user'
import { Document, Warning, Files, Lock } from '@element-plus/icons-vue'

const userStore = useUserStore()
const overview = reactive({})
const alerts = ref([])
const trendRef = ref(), riskRef = ref(), alertChartRef = ref()
let charts = []
const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return '早上好'; if (h < 14) return '中午好'
  if (h < 18) return '下午好'; return '晚上好'
})
function severityType(s) { return s === 'high' ? 'danger' : s === 'medium' ? 'warning' : 'info' }
function severityText(s) { return ({ high: '高', medium: '中', low: '低' })[s] || s }
function statusText(s) { return ({ pending: '未处理', processing: '处理中', resolved: '已处理', false: '误报' })[s] || s }
function makeChart(el, opt) { const c = echarts.init(el); c.setOption(opt); charts.push(c); return c }

async function load() {
  const ov = await dashboardApi.overview(); Object.assign(overview, ov.data)
  const al = await dashboardApi.recentAlerts(8); alerts.value = al.data || []
  await nextTick()
  const trend = await dashboardApi.trend()
  makeChart(trendRef.value, {
    grid: { top: 30, right: 20, bottom: 30, left: 40 }, tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: trend.data.dates, axisLabel: { fontSize: 9, interval: 4 } },
    yAxis: { type: 'value' },
    series: [{ name: '检测', type: 'line', data: trend.data.counts, smooth: true,
      itemStyle: { color: '#1a3a5f' }, areaStyle: { color: 'rgba(26,58,95,0.15)' } }]
  })
  const risk = await dashboardApi.riskLevel()
  makeChart(riskRef.value, {
    tooltip: { trigger: 'item' }, color: ['#f56c6c', '#e6a23c', '#909399', '#67c23a'],
    series: [{ type: 'pie', radius: ['40%', '70%'], label: { fontSize: 10 },
      data: risk.data.levels.map((lv, i) => ({ name: lv, value: risk.data.counts[i] })) }]
  })
  const aSt = await dashboardApi.alertStatus()
  makeChart(alertChartRef.value, { tooltip: { trigger: 'item' },
    color: ['#f56c6c', '#e6a23c', '#67c23a', '#909399'],
    series: [{ type: 'pie', radius: ['40%', '70%'], label: { fontSize: 10 }, data: aSt.data }] })
}
function onResize() { charts.forEach(c => c.resize()) }
onMounted(() => { load(); window.addEventListener('resize', onResize) })
onBeforeUnmount(() => { window.removeEventListener('resize', onResize); charts.forEach(c => c.dispose()) })
</script>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 12px; height: 100%; }
.hero { background: linear-gradient(135deg, #b91c1c 0%, #1a3a5f 100%);
  color: #fff; border-radius: 8px; padding: 18px 24px;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 2px 12px rgba(185,28,28,0.2); }
.hero-title { font-size: 20px; font-weight: 600; margin-bottom: 6px; }
.hero-sub { font-size: 13px; opacity: 0.92; margin-bottom: 10px; }
.hero-tags { display: flex; gap: 8px; }
.hero-right { opacity: 0.5; }

.stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.stat-card { background: #fff; border-radius: 6px; padding: 14px 16px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.stat-icon { width: 44px; height: 44px; border-radius: 8px; color: #fff; display: flex; align-items: center; justify-content: center; }
.stat-label { font-size: 12px; color: #909399; }
.stat-value { font-size: 22px; font-weight: 600; color: #1a3a5f; margin-top: 2px; }

.chart-row { display: flex; gap: 12px; flex: 1; min-height: 0; }
.chart-card { background: #fff; border-radius: 6px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); display: flex; flex-direction: column; }
.chart-card.big { flex: 2; min-height: 0; }
.chart-card.small { flex: 1; min-height: 0; }
.chart-card.mini { flex: 1; min-height: 0; }
.chart-title { font-size: 14px; font-weight: 600; color: #1a3a5f; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }
.chart-body { flex: 1; min-height: 180px; }

.list-card .list-body { flex: 1; overflow-y: auto; }
.alert-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 6px;
  border-bottom: 1px solid #f0f2f5; cursor: pointer; transition: background 0.2s;
}
.alert-item:hover { background: #f7faff; }
.alert-info { flex: 1; min-width: 0; }
.alert-title { font-size: 13px; color: #303133; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.alert-time { font-size: 11px; color: #909399; margin-top: 2px; }
.empty { color: #c0c4cc; text-align: center; padding: 30px 0; font-size: 13px; }
</style>
