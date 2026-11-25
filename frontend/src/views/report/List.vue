<template>
  <div>
    <div class="app-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="报告名称" clearable style="width:200px" />
        <el-select v-model="query.report_type" placeholder="类型" clearable style="width:200px">
          <el-option label="静态检测" value="static" /><el-option label="动态分析" value="dynamic" />
          <el-option label="综合报告" value="comprehensive" />
        </el-select>
        <el-button type="primary" @click="loadData(1)">查询</el-button>
        <el-button @click="onReset">重置</el-button>
        <el-button type="success" @click="dialogVisible = true">生成报告</el-button>
      </div>
      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" />
        <el-table-column prop="title" label="报告名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="report_type" label="类型">
          <template #default="{ row }">{{ typeMap[row.report_type] }}</template>
        </el-table-column>
        <el-table-column prop="related_task_id" label="关联任务" />
        <el-table-column label="风险等级">
          <template #default="{ row }"><span :class="'tag-' + row.risk_level">{{ riskMap[row.risk_level] || row.risk_level }}</span></template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160">
          <template #default="{ row }">{{ $date(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row.id)">查看</el-button>
            <el-button link type="success" @click="downloadReport(row)">下载</el-button>
            <el-button link type="danger" @click="onDel(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination background layout="total, sizes, prev, pager, next, jumper"
          :total="total" v-model:current-page="query.page" v-model:page-size="query.pageSize"
          :page-sizes="[10, 20, 50]" @current-change="loadData()" @size-change="loadData(1)" />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" title="生成报告" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="报告名称"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="报告类型">
          <el-select v-model="form.report_type" style="width:100%;">
            <el-option label="静态检测" value="static" /><el-option label="动态分析" value="dynamic" />
            <el-option label="综合报告" value="comprehensive" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联任务ID" v-if="form.report_type !== 'comprehensive'">
          <el-input-number v-model="form.related_task_id" :min="1" style="width:100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="loading2" @click="onGenerate">生成</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="报告详情" width="900px">
      <pre style="white-space:pre-wrap;background:#f5f7fa;padding:12px;border-radius:4px;font-size:12px;max-height:600px;overflow:auto;">{{ detailJson }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reportApi } from '@/api'

const typeMap = { static: '静态检测', dynamic: '动态分析', comprehensive: '综合报告' }
const query = reactive({ page: 1, pageSize: 10, keyword: '', report_type: '' })
const list = ref([]); const total = ref(0); const loading = ref(false)
const dialogVisible = ref(false); const loading2 = ref(false)
const form = reactive({ title: '安全检测报告', report_type: 'comprehensive', related_task_id: null })
const detailVisible = ref(false); const detailJson = ref('')
const riskMap = { high: '高危', medium: '中危', low: '低危', safe: '安全' }

async function loadData(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const res = await reportApi.page(query)
    list.value = res.data.list; total.value = res.data.total
  } finally { loading.value = false }
}
function onReset() { query.keyword = ''; query.report_type = ''; loadData(1) }

async function onGenerate() {
  if (!form.title) { ElMessage.warning('请输入报告名称'); return }
  loading2.value = true
  try {
    await reportApi.generate({
      title: form.title,
      report_type: form.report_type,
      related_task_id: form.related_task_id
    })
    ElMessage.success('生成成功')
    dialogVisible.value = false; loadData()
  } finally { loading2.value = false }
}

async function showDetail(id) {
  const r = await reportApi.detail(id)
  detailJson.value = JSON.stringify(r.data, null, 2)
  detailVisible.value = true
}

function downloadReport(row) {
  // 报告以JSON形式保存在content字段，打开详情查看
  showDetail(row.id)
}

async function onDel(id) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await reportApi.del(id); ElMessage.success('已删除'); loadData()
}
onMounted(loadData)
</script>
