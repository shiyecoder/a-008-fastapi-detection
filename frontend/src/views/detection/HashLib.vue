<template>
  <div>
    <div class="app-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="哈希/标签关键字" clearable style="width:240px" />
        <el-select v-model="query.severity" placeholder="严重度" clearable style="width:160px">
          <el-option label="高" value="high" /><el-option label="中" value="medium" /><el-option label="低" value="low" />
        </el-select>
        <el-select v-model="query.enabled" placeholder="状态" clearable style="width:160px">
          <el-option label="启用" :value="1" /><el-option label="禁用" :value="0" />
        </el-select>
        <el-button type="primary" @click="loadData(1)">查询</el-button>
        <el-button @click="onReset">重置</el-button>
        <el-button type="success" @click="onAdd">新增哈希</el-button>
      </div>

      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="file_hash" label="SHA256" min-width="280" show-overflow-tooltip />
        <el-table-column prop="label" label="标签/家族" min-width="140" />
        <el-table-column prop="severity" label="严重度" width="90">
          <template #default="{ row }"><span :class="'tag-' + row.severity">{{ riskMap[row.severity] }}</span></template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="130" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-switch :model-value="row.enabled === 1" @change="onToggle(row)" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ $date(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="onEdit(row)">编辑</el-button>
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

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑哈希' : '新增哈希'" width="640px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="SHA256" prop="file_hash">
          <el-input v-model="form.file_hash" placeholder="64 位十六进制" />
        </el-form-item>
        <el-form-item label="标签/家族"><el-input v-model="form.label" placeholder="如：Caidao、Behinder" /></el-form-item>
        <el-form-item label="严重度" prop="severity">
          <el-select v-model="form.severity" style="width:100%;">
            <el-option label="高" value="high" /><el-option label="中" value="medium" /><el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源"><el-input v-model="form.source" placeholder="如：VirusTotal、应急响应" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { hashLibApi } from '@/api'

const riskMap = { high: '高', medium: '中', low: '低' }
const query = reactive({ page: 1, pageSize: 10, keyword: '', severity: '', enabled: '' })
const list = ref([]); const total = ref(0); const loading = ref(false)
const dialogVisible = ref(false); const formRef = ref()
const form = reactive({ id: null, file_hash: '', label: '', severity: 'high', source: '', description: '', enabled: 1 })
const rules = {
  file_hash: [
    { required: true, message: '请输入 SHA256 哈希' },
    { pattern: /^[0-9a-fA-F]{64}$/, message: '必须是 64 位十六进制' }
  ],
  severity: [{ required: true }]
}

async function loadData(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const params = { ...query }
    if (params.enabled === '' || params.enabled === null) delete params.enabled
    if (!params.keyword) delete params.keyword
    if (!params.severity) delete params.severity
    const res = await hashLibApi.page(params)
    list.value = res.data.list; total.value = res.data.total
  } finally { loading.value = false }
}

function onReset() { query.keyword = ''; query.severity = ''; query.enabled = ''; loadData(1) }

function onAdd() {
  Object.assign(form, { id: null, file_hash: '', label: '', severity: 'high', source: '', description: '', enabled: 1 })
  dialogVisible.value = true
}

function onEdit(row) {
  Object.assign(form, row)
  dialogVisible.value = true
}

async function onSave() {
  await formRef.value.validate()
  if (form.id) await hashLibApi.update(form.id, form)
  else await hashLibApi.add(form)
  ElMessage.success('保存成功')
  dialogVisible.value = false
  loadData()
}

async function onDel(id) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await hashLibApi.del(id); ElMessage.success('已删除'); loadData()
}

async function onToggle(row) {
  await hashLibApi.toggle(row.id); loadData()
}

onMounted(loadData)
</script>
