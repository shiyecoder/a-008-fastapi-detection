<template>
  <div>
    <div class="app-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="文件名" clearable style="width:200px" />
        <el-select v-model="query.status" placeholder="状态" clearable style="width:200px">
          <el-option label="已隔离" value="quarantined" />
          <el-option label="已恢复" value="restored" />
          <el-option label="已删除" value="deleted" />
        </el-select>
        <el-button type="primary" @click="loadData(1)">查询</el-button>
        <el-button @click="onReset">重置</el-button>
      </div>
      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" />
        <el-table-column prop="file_name" label="文件名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="origin_path" label="原路径" min-width="200" show-overflow-tooltip />
        <el-table-column prop="file_size" label="大小(B)" />
        <el-table-column prop="hit_rule" label="命中规则" min-width="140" show-overflow-tooltip />
        <el-table-column prop="risk_level" label="风险等级">
          <template #default="{ row }"><span :class="'tag-' + row.risk_level">{{ riskMap[row.risk_level] }}</span></template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">{{ statusMap[row.status] }}</template>
        </el-table-column>
        <el-table-column label="隔离时间" min-width="160">
          <template #default="{ row }">{{ $date(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="row.status !== 'quarantined'" @click="onRestore(row.id)">恢复</el-button>
            <el-button link type="danger" :disabled="row.status === 'deleted'" @click="onDel(row.id)">彻底删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination background layout="total, sizes, prev, pager, next, jumper"
          :total="total" v-model:current-page="query.page" v-model:page-size="query.pageSize"
          :page-sizes="[10, 20, 50]" @current-change="loadData()" @size-change="loadData(1)" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { quarantineApi } from '@/api'

const query = reactive({ page: 1, pageSize: 10, keyword: '', status: '' })
const list = ref([]); const total = ref(0); const loading = ref(false)
const riskMap = { high: '高危', medium: '中危', low: '低危', safe: '安全' }
const statusMap = { quarantined: '已隔离', restored: '已恢复', deleted: '已删除' }

async function loadData(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const res = await quarantineApi.page(query)
    list.value = res.data.list; total.value = res.data.total
  } finally { loading.value = false }
}
function onReset() { query.keyword = ''; query.status = ''; loadData(1) }

async function onRestore(id) {
  await ElMessageBox.confirm('确认恢复？', '提示', { type: 'warning' })
  await quarantineApi.restore(id); ElMessage.success('已恢复'); loadData()
}
async function onDel(id) {
  await ElMessageBox.confirm('彻底删除后无法恢复，确认？', '提示', { type: 'warning' })
  await quarantineApi.del(id); ElMessage.success('已删除'); loadData()
}
onMounted(loadData)
</script>
