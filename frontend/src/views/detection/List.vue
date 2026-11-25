<template>
  <div>
    <div class="app-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="文件名" clearable style="width:200px" />
        <el-select v-model="query.detect_type" placeholder="检测类型" clearable style="width:200px">
          <el-option label="静态" value="static" /><el-option label="动态" value="dynamic" /><el-option label="混合" value="mixed" />
        </el-select>
        <el-select v-model="query.risk_level" placeholder="风险等级" clearable style="width:200px">
          <el-option label="高危" value="high" /><el-option label="中危" value="medium" />
          <el-option label="低危" value="low" /><el-option label="安全" value="safe" />
        </el-select>
        <el-button type="primary" @click="loadData(1)">查询</el-button>
        <el-button @click="onReset">重置</el-button>
      </div>

      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" />
        <el-table-column prop="file_name" label="文件名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="language" label="语言" />
        <el-table-column prop="detect_type" label="检测类型">
          <template #default="{ row }">{{ ({static:'静态',dynamic:'动态',mixed:'混合'})[row.detect_type] }}</template>
        </el-table-column>
        <el-table-column label="风险等级">
          <template #default="{ row }">
            <span :class="'tag-' + row.risk_level">{{ riskMap[row.risk_level] }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="hit_count" label="命中数" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">{{ statusMap[row.status] || row.status }}</template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要" min-width="180" show-overflow-tooltip />
        <el-table-column label="提交时间" min-width="160">
          <template #default="{ row }">{{ $date(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row.id)">详情</el-button>
            <el-button link type="success" @click="showScope(row.id)">感染范围</el-button>
            <el-button link type="warning" @click="onQuarantine(row)">隔离</el-button>
            <el-button link type="danger" @click="onDel(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background layout="total, sizes, prev, pager, next, jumper"
          :total="total" v-model:current-page="query.page" v-model:page-size="query.pageSize"
          :page-sizes="[10, 20, 50, 100]" @current-change="loadData()" @size-change="loadData(1)"
        />
      </div>
    </div>

    <el-dialog v-model="detailVisible" title="检测详情" width="960px">
      <div v-if="detailData.task">
        <el-descriptions :column="3" border size="small" style="margin-bottom:12px;">
          <el-descriptions-item label="任务">{{ detailData.task.task_name }}</el-descriptions-item>
          <el-descriptions-item label="文件">{{ detailData.task.file_name }}</el-descriptions-item>
          <el-descriptions-item label="语言">{{ detailData.task.language }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ detailData.task.detect_type }}</el-descriptions-item>
          <el-descriptions-item label="风险"><el-tag :type="riskTagType(detailData.task.risk_level)">{{ riskMap[detailData.task.risk_level] || detailData.task.risk_level }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="哈希">{{ detailData.task.file_hash }}</el-descriptions-item>
          <el-descriptions-item label="摘要" :span="3">{{ detailData.task.summary }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:12px 0 8px;">命中规则与修复建议（{{ detailData.findings.length }}条）</h4>
        <el-table :data="detailData.findings" size="small" max-height="380">
          <el-table-column prop="rule_name" label="规则" min-width="160" />
          <el-table-column prop="rule_type" label="类型" width="90" />
          <el-table-column prop="severity" label="等级" width="80">
            <template #default="{ row }"><el-tag :type="riskTagType(row.severity)" size="small">{{ row.severity }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="line_no" label="行号" width="60" />
          <el-table-column prop="code_snippet" label="代码片段" min-width="200" show-overflow-tooltip />
          <el-table-column prop="description" label="说明" min-width="180" show-overflow-tooltip />
          <el-table-column prop="fix_advice" label="修复建议" min-width="200" show-overflow-tooltip />
          <el-table-column label="补丁/参考" width="110">
            <template #default="{ row }">
              <el-link v-if="row.fix_mapping?.patch_url" :href="row.fix_mapping.patch_url" target="_blank" type="primary">补丁</el-link>
              <el-link v-if="row.fix_mapping?.reference" :href="row.fix_mapping.reference" target="_blank" type="info" style="margin-left:6px;">参考</el-link>
              <span v-if="!row.fix_mapping" style="color:#999;">-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <pre v-else style="white-space:pre-wrap;background:#f5f7fa;padding:12px;border-radius:4px;font-size:12px;max-height:600px;overflow:auto;">{{ detailJson }}</pre>
    </el-dialog>

    <el-dialog v-model="scopeVisible" title="感染范围定位" width="820px">
      <el-alert v-if="scopeData.origin" :title="`原文件: ${scopeData.origin.file_name}  | 范围内可疑文件: ${scopeData.scope_count} 个`" type="warning" :closable="false" style="margin-bottom:12px;" />
      <el-table :data="scopeData.related_files" size="small" max-height="460" empty-text="无关联可疑文件">
        <el-table-column prop="id" label="任务ID" width="80" />
        <el-table-column prop="file_name" label="文件名" min-width="160" />
        <el-table-column prop="file_path" label="路径" min-width="200" show-overflow-tooltip />
        <el-table-column label="风险" width="80">
          <template #default="{ row }"><el-tag :type="riskTagType(row.risk_level)" size="small">{{ riskMap[row.risk_level] || row.risk_level }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="match_reason" label="匹配原因" min-width="180" />
        <el-table-column label="时间" width="160">
          <template #default="{ row }">{{ $date(row.create_time) }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { detectionApi } from '@/api'

const query = reactive({ page: 1, pageSize: 10, keyword: '', detect_type: '', risk_level: '' })
const list = ref([])
const total = ref(0)
const loading = ref(false)
const detailVisible = ref(false)
const detailJson = ref('')
const detailData = ref({ task: null, findings: [] })
const scopeVisible = ref(false)
const scopeData = ref({ origin: null, scope_count: 0, related_files: [] })
const riskMap = { high: '高危', medium: '中危', low: '低危', safe: '安全' }
const statusMap = { pending: '待检测', running: '检测中', finished: '完成', failed: '失败' }
function riskTagType(r) { return ({ high: 'danger', medium: 'warning', low: 'info', safe: 'success' })[r] || 'info' }

async function loadData(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const res = await detectionApi.page(query)
    list.value = res.data.list
    total.value = res.data.total
  } finally { loading.value = false }
}

function onReset() {
  query.keyword = ''; query.detect_type = ''; query.risk_level = ''
  loadData(1)
}

async function showDetail(id) {
  const r = await detectionApi.detail(id)
  detailData.value = r.data
  detailJson.value = JSON.stringify(r.data, null, 2)
  detailVisible.value = true
}

async function showScope(id) {
  const r = await detectionApi.scope(id)
  scopeData.value = r.data
  scopeVisible.value = true
}

async function onDel(id) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await detectionApi.del(id)
  ElMessage.success('已删除')
  loadData()
}

async function onQuarantine(row) {
  await ElMessageBox.confirm(`确认将文件 [${row.file_name}] 加入隔离区？`, '提示', { type: 'warning' })
  await detectionApi.quarantine(row.id)
  ElMessage.success('已隔离')
  loadData()
}

onMounted(loadData)
</script>
