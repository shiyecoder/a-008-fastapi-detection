<template>
  <div class="dashboard">
    <!-- 普通用户欢迎横幅 -->
    <div class="hero">
      <div class="hero-left">
        <div class="hero-title">{{ greeting }}，{{ userStore.nickname || userStore.username }}</div>
        <div class="hero-sub">欢迎回到 Webshell 检测平台 · 上传文件即可发起静态/动态检测，识别可疑代码</div>
        <div class="hero-tags">
          <el-button type="primary" size="small" @click="$router.push('/detection/scan')">
            <el-icon><Upload /></el-icon><span style="margin-left:4px">立即检测</span>
          </el-button>
          <el-button size="small" @click="$router.push('/detection/list')">我的检测记录</el-button>
          <el-button size="small" @click="$router.push('/report/list')">查看报告</el-button>
        </div>
      </div>
      <div class="hero-right"><el-icon :size="64"><User /></el-icon></div>
    </div>

    <!-- 个人统计卡片 -->
    <div class="stat-row">
      <div class="stat-card">
        <div class="stat-icon" style="background:#1a3a5f"><el-icon :size="22"><Document /></el-icon></div>
        <div class="stat-info"><div class="stat-label">我的检测任务</div><div class="stat-value">{{ stats.myTasks }}</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#f56c6c"><el-icon :size="22"><Warning /></el-icon></div>
        <div class="stat-info"><div class="stat-label">高/中危发现</div><div class="stat-value">{{ stats.myHigh }}</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#67c23a"><el-icon :size="22"><CircleCheck /></el-icon></div>
        <div class="stat-info"><div class="stat-label">安全文件</div><div class="stat-value">{{ stats.mySafe }}</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#409eff"><el-icon :size="22"><DataLine /></el-icon></div>
        <div class="stat-info"><div class="stat-label">检测覆盖率</div><div class="stat-value">{{ coverage }}%</div></div>
      </div>
    </div>

    <!-- 主体：左近14天趋势 + 右近期任务列表 -->
    <div class="chart-row">
      <div class="chart-card big">
        <div class="chart-title">我的近14天检测趋势</div>
        <div ref="trendRef" class="chart-body"></div>
      </div>
      <div class="chart-card small list-card">
        <div class="chart-title">最近检测记录</div>
        <div class="list-body">
          <div v-if="!stats.recent || !stats.recent.length" class="empty">
            尚未提交检测，<el-link type="primary" @click="$router.push('/detection/scan')">立即检测</el-link>
          </div>
          <div v-for="r in stats.recent" :key="r.id" class="task-item" @click="$router.push('/detection/list')">
            <el-tag :type="riskType(r.risk_level)" size="small" effect="dark" style="flex-shrink:0">{{ riskText(r.risk_level) }}</el-tag>
            <div class="task-info">
              <div class="task-name">{{ r.file_name }}</div>
              <div class="task-time">{{ typeText(r.detect_type) }} · {{ $date(r.create_time) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 提示卡片 -->
    <div class="tips-row">
      <div class="tip-card">
        <el-icon :size="22" color="#409eff"><DocumentAdd /></el-icon>
        <div>
          <div class="tip-title">支持多语言静态检测</div>
          <div class="tip-text">PHP / JSP / ASP / Python 自动语言识别</div>
        </div>
      </div>
      <div class="tip-card">
        <el-icon :size="22" color="#e6a23c"><Cpu /></el-icon>
        <div>
          <div class="tip-title">沙箱动态行为检测</div>
          <div class="tip-text">监控文件、进程、网络、敏感函数</div>
        </div>
      </div>
      <div class="tip-card">
        <el-icon :size="22" color="#67c23a"><Reading /></el-icon>
        <div>
          <div class="tip-title">检测后自动关联修复方案</div>
          <div class="tip-text">命中漏洞将自动给出修复建议与补丁</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi } from '@/api'
import { useUserStore } from '@/store/user'
import { Document, Warning, CircleCheck, DataLine, User, Upload, DocumentAdd, Cpu, Reading } from '@element-plus/icons-vue'

const userStore = useUserStore()
const stats = reactive({ myTasks: 0, myHigh: 0, mySafe: 0, recent: [] })
const trendRef = ref()
let chart = null

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return '早上好'; if (h < 14) return '中午好'
  if (h < 18) return '下午好'; return '晚上好'
})
const coverage = computed(() => {
  const t = stats.myTasks
  if (!t) return 0
  return Math.min(100, Math.round((stats.mySafe / t) * 100))
})
function riskType(r) { return r === 'high' ? 'danger' : r === 'medium' ? 'warning' : r === 'low' ? 'info' : 'success' }
function riskText(r) { return ({ high: '高', medium: '中', low: '低', safe: '安全' })[r] || r || '-' }
function typeText(t) { return ({ static: '静态', dynamic: '动态', mixed: '混合' })[t] || t }

async function load() {
  const r = await dashboardApi.myStats()
  Object.assign(stats, r.data)
  await nextTick()
  const t = await dashboardApi.myTrend()
  chart = echarts.init(trendRef.value)
  chart.setOption({
    grid: { top: 30, right: 20, bottom: 30, left: 40 },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: t.data.dates, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ name: '检测', type: 'bar', data: t.data.counts, itemStyle: { color: '#1a3a5f' }, barWidth: '40%' }]
  })
}
function onResize() { chart?.resize() }
onMounted(() => { load(); window.addEventListener('resize', onResize) })
onBeforeUnmount(() => { window.removeEventListener('resize', onResize); chart?.dispose() })
</script>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 12px; height: 100%; }
.hero { background: linear-gradient(135deg, #1a3a5f 0%, #4a90e2 100%);
  color: #fff; border-radius: 8px; padding: 18px 24px;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 2px 12px rgba(26,58,95,0.2); }
.hero-title { font-size: 20px; font-weight: 600; margin-bottom: 6px; }
.hero-sub { font-size: 13px; opacity: 0.9; margin-bottom: 12px; }
.hero-tags { display: flex; gap: 8px; }
.hero-right { opacity: 0.5; }

.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.stat-card { background: #fff; border-radius: 6px; padding: 14px 16px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.stat-icon { width: 44px; height: 44px; border-radius: 8px; color: #fff; display: flex; align-items: center; justify-content: center; }
.stat-label { font-size: 12px; color: #909399; }
.stat-value { font-size: 22px; font-weight: 600; color: #1a3a5f; margin-top: 2px; }

.chart-row { display: flex; gap: 12px; flex: 1; min-height: 0; }
.chart-card { background: #fff; border-radius: 6px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); display: flex; flex-direction: column; }
.chart-card.big { flex: 2; min-height: 0; }
.chart-card.small { flex: 1; min-height: 0; }
.chart-title { font-size: 14px; font-weight: 600; color: #1a3a5f; margin-bottom: 8px; }
.chart-body { flex: 1; min-height: 200px; }

.list-card .list-body { flex: 1; overflow-y: auto; }
.task-item { display: flex; align-items: center; gap: 8px; padding: 8px 6px; border-bottom: 1px solid #f0f2f5; cursor: pointer; }
.task-item:hover { background: #f7faff; }
.task-info { flex: 1; min-width: 0; }
.task-name { font-size: 13px; color: #303133; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.task-time { font-size: 11px; color: #909399; margin-top: 2px; }
.empty { color: #909399; text-align: center; padding: 30px 0; font-size: 13px; }

.tips-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.tip-card { background: #fff; border-radius: 6px; padding: 14px 16px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.tip-title { font-size: 13px; font-weight: 600; color: #1a3a5f; margin-bottom: 2px; }
.tip-text { font-size: 12px; color: #909399; }
</style>
