<template>
  <div>
    <div class="app-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="告警标题" clearable style="width:200px" />
        <el-select v-model="query.severity" placeholder="级别" clearable style="width:200px">
          <el-option label="高危" value="high" /><el-option label="中危" value="medium" /><el-option label="低危" value="low" />
        </el-select>
        <el-select v-model="query.status" placeholder="状态" clearable style="width:200px">
          <el-option label="待处理" value="pending" /><el-option label="处理中" value="processing" />
          <el-option label="已处理" value="resolved" /><el-option label="误报" value="false_positive" />
        </el-select>
        <el-button type="primary" @click="loadData(1)">查询</el-button>
        <el-button @click="onReset">重置</el-button>
      </div>
      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" />
        <el-table-column prop="title" label="告警标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="alert_type" label="类型" />
        <el-table-column label="级别">
          <template #default="{ row }"><span :class="'tag-' + row.severity">{{ riskMap[row.severity] }}</span></template>
        </el-table-column>
        <el-table-column prop="source" label="来源" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">{{ statusMap[row.status] }}</template>
        </el-table-column>
        <el-table-column prop="handler" label="处理人" />
        <el-table-column label="告警时间">
          <template #default="{ row }">{{ $date(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="onHandle(row)" :disabled="row.status === 'resolved' || row.status === 'false_positive'">处理</el-button>
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

    <el-dialog v-model="dialogVisible" title="处理告警" width="500px">
      <el-form :model="handleForm" label-width="80px">
        <el-form-item label="处理结果">
          <el-radio-group v-model="handleForm.status">
            <el-radio value="resolved">已处理</el-radio>
            <el-radio value="false_positive">误报</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="handleForm.handle_remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { alertApi } from '@/api'

const query = reactive({ page: 1, pageSize: 10, keyword: '', severity: '', status: '' })
const list = ref([]); const total = ref(0); const loading = ref(false)
const riskMap = { high: '高危', medium: '中危', low: '低危' }
const statusMap = { pending: '待处理', processing: '处理中', resolved: '已处理', false_positive: '误报' }
const dialogVisible = ref(false)
const handleForm = reactive({ id: null, status: 'resolved', handle_remark: '' })

async function loadData(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const res = await alertApi.page(query)
    list.value = res.data.list; total.value = res.data.total
  } finally { loading.value = false }
}
function onReset() { query.keyword = ''; query.severity = ''; query.status = ''; loadData(1) }

function onHandle(row) {
  handleForm.id = row.id; handleForm.status = 'resolved'; handleForm.handle_remark = ''
  dialogVisible.value = true
}

async function onSubmit() {
  await alertApi.handle(handleForm.id, { status: handleForm.status, handle_remark: handleForm.handle_remark })
  ElMessage.success('处理成功')
  dialogVisible.value = false; loadData()
}

async function onDel(id) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await alertApi.del(id); ElMessage.success('已删除'); loadData()
}

onMounted(loadData)
</script>
