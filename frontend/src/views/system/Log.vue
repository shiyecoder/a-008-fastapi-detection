<template>
  <div>
    <div class="app-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="操作内容/用户" clearable />
        <el-select v-model="query.module" placeholder="模块" clearable style="width:200px">
          <el-option label="认证" value="认证" />
          <el-option label="检测" value="检测" />
          <el-option label="告警" value="告警" />
          <el-option label="隔离" value="隔离" />
          <el-option label="报告" value="报告" />
          <el-option label="系统" value="系统" />
        </el-select>
        <el-button type="primary" @click="loadData(1)">查询</el-button>
        <el-button @click="onReset">重置</el-button>
        <el-button type="danger" @click="onClear">清空日志</el-button>
      </div>
      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" />
        <el-table-column prop="username" label="用户" />
        <el-table-column prop="module" label="模块" />
        <el-table-column prop="operation" label="操作" min-width="160" show-overflow-tooltip />
        <el-table-column prop="method" label="方法" />
        <el-table-column prop="url" label="路径" min-width="200" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" />
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">{{ row.status === 1 ? '成功' : '失败' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ $date(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="onDel(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination background layout="total, sizes, prev, pager, next, jumper"
          :total="total" v-model:current-page="query.page" v-model:page-size="query.pageSize"
          :page-sizes="[10, 20, 50, 100]" @current-change="loadData()" @size-change="loadData(1)" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { logApi } from '@/api'

const query = reactive({ page: 1, pageSize: 10, keyword: '', module: '' })
const list = ref([]); const total = ref(0); const loading = ref(false)

async function loadData(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const res = await logApi.page(query)
    list.value = res.data.list; total.value = res.data.total
  } finally { loading.value = false }
}
function onReset() { query.keyword = ''; query.module = ''; loadData(1) }
async function onDel(id) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await logApi.del(id); ElMessage.success('已删除'); loadData()
}
async function onClear() {
  await ElMessageBox.confirm('确认清空全部日志？此操作不可恢复', '提示', { type: 'warning' })
  await logApi.clear(); ElMessage.success('已清空'); loadData()
}

onMounted(loadData)
</script>
