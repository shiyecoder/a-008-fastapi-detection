<template>
  <div>
    <div class="app-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="规则名称" clearable style="width:200px" />
        <el-select v-model="query.language" placeholder="语言" clearable style="width:200px">
          <el-option v-for="l in langs" :key="l" :label="l" :value="l" />
        </el-select>
        <el-select v-model="query.enabled" placeholder="状态" clearable style="width:200px">
          <el-option label="启用" :value="1" /><el-option label="禁用" :value="0" />
        </el-select>
        <el-button type="primary" @click="loadData(1)">查询</el-button>
        <el-button @click="onReset">重置</el-button>
        <el-button type="success" @click="onAdd">新增规则</el-button>
      </div>

      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" />
        <el-table-column prop="rule_name" label="规则名称" min-width="160" />
        <el-table-column prop="language" label="语言" />
        <el-table-column prop="severity" label="严重度">
          <template #default="{ row }"><span :class="'tag-' + row.severity">{{ riskMap[row.severity] }}</span></template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-switch :model-value="row.enabled === 1" @change="onToggle(row)" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间">
          <template #default="{ row }">{{ $date(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
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

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑规则' : '新增规则'" width="640px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="规则名称" prop="rule_name"><el-input v-model="form.rule_name" /></el-form-item>
        <el-form-item label="语言" prop="language">
          <el-select v-model="form.language" style="width:100%;">
            <el-option v-for="l in langs" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重度" prop="severity">
          <el-select v-model="form.severity" style="width:100%;">
            <el-option label="高" value="high" /><el-option label="中" value="medium" /><el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="规则内容" prop="pattern">
          <el-input v-model="form.pattern" type="textarea" :rows="4" placeholder="正则表达式或YARA规则" />
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
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
import { yaraApi } from '@/api'

const langs = ['php', 'jsp', 'asp', 'python', 'java', 'all']
const riskMap = { high: '高', medium: '中', low: '低' }
const query = reactive({ page: 1, pageSize: 10, keyword: '', language: '', enabled: '' })
const list = ref([]); const total = ref(0); const loading = ref(false)
const dialogVisible = ref(false); const formRef = ref()
const form = reactive({ id: null, rule_name: '', language: 'php', severity: 'medium', pattern: '', description: '', enabled: 1 })
const rules = {
  rule_name: [{ required: true, message: '请输入规则名称' }],
  language: [{ required: true }],
  pattern: [{ required: true, message: '请输入规则内容' }]
}

async function loadData(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const params = { ...query }
    if (params.enabled === '' || params.enabled === null) delete params.enabled
    if (!params.keyword) delete params.keyword
    if (!params.language) delete params.language
    const res = await yaraApi.page(params)
    list.value = res.data.list; total.value = res.data.total
  } finally { loading.value = false }
}

function onReset() { query.keyword = ''; query.language = ''; query.enabled = ''; loadData(1) }

function onAdd() {
  Object.assign(form, { id: null, rule_name: '', language: 'php', severity: 'medium', pattern: '', description: '', enabled: 1 })
  dialogVisible.value = true
}

function onEdit(row) {
  Object.assign(form, row)
  dialogVisible.value = true
}

async function onSave() {
  await formRef.value.validate()
  if (form.id) await yaraApi.update(form.id, form)
  else await yaraApi.add(form)
  ElMessage.success('保存成功')
  dialogVisible.value = false
  loadData()
}

async function onDel(id) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await yaraApi.del(id); ElMessage.success('已删除'); loadData()
}

async function onToggle(row) {
  await yaraApi.toggle(row.id); loadData()
}

onMounted(loadData)
</script>
