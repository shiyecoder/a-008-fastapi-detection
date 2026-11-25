<template>
  <div>
    <div class="app-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="漏洞类型" clearable style="width:200px" />
        <el-select v-model="query.severity" placeholder="严重度" clearable style="width:200px">
          <el-option label="高" value="high" /><el-option label="中" value="medium" /><el-option label="低" value="low" />
        </el-select>
        <el-button type="primary" @click="loadData(1)">查询</el-button>
        <el-button @click="onReset">重置</el-button>
        <el-button type="success" @click="onAdd">新增</el-button>
      </div>
      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" />
        <el-table-column prop="vuln_type" label="漏洞类型" min-width="180" />
        <el-table-column label="严重度">
          <template #default="{ row }"><span :class="'tag-' + row.severity">{{ severityMap[row.severity] }}</span></template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="fix_advice" label="修复建议" min-width="200" show-overflow-tooltip />
        <el-table-column prop="patch_url" label="补丁链接" min-width="160" show-overflow-tooltip />
        <el-table-column prop="reference" label="参考链接" min-width="200" show-overflow-tooltip />
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
          :page-sizes="[10, 20, 50]" @current-change="loadData()" @size-change="loadData(1)" />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑' : '新增'" width="640px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="漏洞类型" prop="vuln_type"><el-input v-model="form.vuln_type" /></el-form-item>
        <el-form-item label="严重度" prop="severity">
          <el-select v-model="form.severity" style="width:100%;">
            <el-option label="高" value="high" /><el-option label="中" value="medium" /><el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="修复建议"><el-input v-model="form.fix_advice" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="补丁链接"><el-input v-model="form.patch_url" /></el-form-item>
        <el-form-item label="参考链接"><el-input v-model="form.reference" /></el-form-item>
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
import { vulnFixApi } from '@/api'

const query = reactive({ page: 1, pageSize: 10, keyword: '', severity: '' })
const list = ref([]); const total = ref(0); const loading = ref(false)
const severityMap = { high: '高', medium: '中', low: '低' }
const dialogVisible = ref(false); const formRef = ref()
const form = reactive({ id: null, vuln_type: '', severity: 'medium', description: '', fix_advice: '', patch_url: '', reference: '' })
const rules = {
  vuln_type: [{ required: true, message: '请输入漏洞类型' }]
}

async function loadData(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const res = await vulnFixApi.page(query)
    list.value = res.data.list; total.value = res.data.total
  } finally { loading.value = false }
}
function onReset() { query.keyword = ''; query.severity = ''; loadData(1) }

function onAdd() {
  Object.assign(form, { id: null, vuln_type: '', severity: 'medium', description: '', fix_advice: '', patch_url: '', reference: '' })
  dialogVisible.value = true
}
function onEdit(row) { Object.assign(form, row); dialogVisible.value = true }

async function onSave() {
  await formRef.value.validate()
  if (form.id) await vulnFixApi.update(form.id, form)
  else await vulnFixApi.add(form)
  ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
}
async function onDel(id) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await vulnFixApi.del(id); ElMessage.success('已删除'); loadData()
}
onMounted(loadData)
</script>
