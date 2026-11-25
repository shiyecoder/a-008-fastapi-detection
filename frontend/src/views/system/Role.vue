<template>
  <div>
    <div class="app-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="角色名" clearable style="width:200px" />
        <el-button type="primary" @click="loadData(1)">查询</el-button>
        <el-button @click="onReset">重置</el-button>
        <el-button type="success" @click="onAdd">新增角色</el-button>
      </div>
      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" />
        <el-table-column prop="role_name" label="角色名" />
        <el-table-column prop="role_code" label="编码" />
        <el-table-column prop="remark" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160">
          <template #default="{ row }">{{ $date(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="onAssignMenu(row)">分配菜单</el-button>
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

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑角色' : '新增角色'" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="角色名" prop="role_name"><el-input v-model="form.role_name" /></el-form-item>
        <el-form-item label="编码" prop="role_code"><el-input v-model="form.role_code" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="menuDialog" title="分配菜单" width="500px">
      <el-tree
        ref="treeRef"
        :data="menuTree"
        show-checkbox
        node-key="id"
        :default-checked-keys="checkedKeys"
        :props="{ label: 'name', children: 'children' }"
      />
      <template #footer>
        <el-button @click="menuDialog = false">取消</el-button>
        <el-button type="primary" @click="onSaveMenu">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { roleApi, menuApi } from '@/api'

const query = reactive({ page: 1, pageSize: 10, keyword: '' })
const list = ref([]); const total = ref(0); const loading = ref(false)
const dialogVisible = ref(false); const formRef = ref()
const form = reactive({ id: null, role_name: '', role_code: '', remark: '', status: 1 })
const rules = {
  role_name: [{ required: true, message: '请输入角色名' }],
  role_code: [{ required: true, message: '请输入编码' }]
}

const menuDialog = ref(false); const menuTree = ref([]); const checkedKeys = ref([])
const treeRef = ref(); const currentRoleId = ref(null)

async function loadData(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const res = await roleApi.page(query)
    list.value = res.data.list; total.value = res.data.total
  } finally { loading.value = false }
}
function onReset() { query.keyword = ''; loadData(1) }

function onAdd() {
  Object.assign(form, { id: null, role_name: '', role_code: '', remark: '', status: 1 })
  dialogVisible.value = true
}
function onEdit(row) { Object.assign(form, row); dialogVisible.value = true }

async function onSave() {
  await formRef.value.validate()
  if (form.id) await roleApi.update(form.id, form)
  else await roleApi.add(form)
  ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
}

async function onDel(id) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await roleApi.del(id); ElMessage.success('已删除'); loadData()
}

// 过滤掉"菜单管理"节点（按需求隐藏）
function filterMenuMgmt(arr) {
  return arr.filter(m => m.name !== '菜单管理').map(m => ({
    ...m, children: m.children ? filterMenuMgmt(m.children) : []
  }))
}

async function onAssignMenu(row) {
  currentRoleId.value = row.id
  const t = await menuApi.tree()
  menuTree.value = filterMenuMgmt(t.data)
  const c = await roleApi.getMenus(row.id)
  checkedKeys.value = c.data
  menuDialog.value = true
}

async function onSaveMenu() {
  const ids = treeRef.value.getCheckedKeys().concat(treeRef.value.getHalfCheckedKeys())
  await roleApi.assignMenu(currentRoleId.value, ids)
  ElMessage.success('保存成功')
  menuDialog.value = false
}

onMounted(loadData)
</script>
