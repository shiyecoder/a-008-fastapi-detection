<template>
  <div>
    <div class="app-card">
      <div class="toolbar">
        <el-button type="success" @click="onAdd(null)">新增菜单</el-button>
      </div>
      <el-table :data="list" row-key="id" :tree-props="{ children: 'children' }" default-expand-all stripe>
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="path" label="路由" min-width="180" />
        <el-table-column prop="icon" label="图标" />
        <el-table-column prop="menu_type" label="类型">
          <template #default="{ row }">{{ row.menu_type === 1 ? '菜单' : '按钮' }}</template>
        </el-table-column>
        <el-table-column prop="perms" label="权限标识" min-width="150" />
        <el-table-column prop="sort" label="排序" />
        <el-table-column label="可见">
          <template #default="{ row }">{{ row.visible === 1 ? '是' : '否' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="onAdd(row.id)">新增子项</el-button>
            <el-button link type="primary" @click="onEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="onDel(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑菜单' : '新增菜单'" width="560px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="父级">
          <el-input :value="parentName" disabled />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="form.menu_type">
            <el-radio :value="1">菜单</el-radio>
            <el-radio :value="2">按钮</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="路由"><el-input v-model="form.path" /></el-form-item>
        <el-form-item label="组件"><el-input v-model="form.component" /></el-form-item>
        <el-form-item label="图标"><el-input v-model="form.icon" /></el-form-item>
        <el-form-item label="权限标识"><el-input v-model="form.perms" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort" :min="0" /></el-form-item>
        <el-form-item label="可见"><el-switch v-model="form.visible" :active-value="1" :inactive-value="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { menuApi } from '@/api'

const list = ref([])
const dialogVisible = ref(false); const formRef = ref()
const form = reactive({ id: null, parent_id: 0, name: '', menu_type: 1, path: '', component: '', icon: '', perms: '', sort: 0, visible: 1 })
const rules = { name: [{ required: true, message: '请输入名称' }] }

const parentName = computed(() => {
  if (form.parent_id === 0) return '根目录'
  const find = (arr) => {
    for (const m of arr) {
      if (m.id === form.parent_id) return m.name
      if (m.children) { const r = find(m.children); if (r) return r }
    }
  }
  return find(list.value) || '-'
})

async function loadData() {
  const res = await menuApi.tree()
  list.value = res.data
}

function onAdd(parentId) {
  Object.assign(form, { id: null, parent_id: parentId || 0, name: '', menu_type: 1, path: '', component: '', icon: '', perms: '', sort: 0, visible: 1 })
  dialogVisible.value = true
}
function onEdit(row) { Object.assign(form, row); dialogVisible.value = true }

async function onSave() {
  await formRef.value.validate()
  if (form.id) await menuApi.update(form.id, form)
  else await menuApi.add(form)
  ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
}

async function onDel(id) {
  await ElMessageBox.confirm('确认删除？子项也会被删除', '提示', { type: 'warning' })
  await menuApi.del(id); ElMessage.success('已删除'); loadData()
}

onMounted(loadData)
</script>
