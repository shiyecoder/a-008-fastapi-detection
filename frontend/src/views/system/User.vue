<template>
  <div>
    <div class="app-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="用户名/昵称" clearable style="width:200px" />
        <el-select v-model="query.status" placeholder="状态" clearable style="width:200px">
          <el-option label="启用" :value="1" /><el-option label="禁用" :value="0" />
        </el-select>
        <el-button type="primary" @click="loadData(1)">查询</el-button>
        <el-button @click="onReset">重置</el-button>
        <el-button type="success" @click="onAdd">新增用户</el-button>
      </div>
      <el-table :data="list" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" />
        <el-table-column label="头像">
          <template #default="{ row }">
            <el-avatar :size="32" :src="row.avatar ? '/uploads/' + row.avatar : ''">
              <el-icon><User /></el-icon>
            </el-avatar>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="nickname" label="昵称" />
        <el-table-column prop="email" label="邮箱" min-width="160" />
        <el-table-column prop="phone" label="手机号" />
        <el-table-column label="角色" min-width="120">
          <template #default="{ row }">
            <el-tag v-for="r in row.role_names" :key="r" size="small" style="margin-right:4px;">{{ r }}</el-tag>
          </template>
        </el-table-column>
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
            <el-button link type="primary" @click="onEdit(row)">编辑</el-button>
            <el-button link type="warning" @click="onResetPwd(row)">重置密码</el-button>
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

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑用户' : '新增用户'" width="560px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="头像">
          <el-upload :show-file-list="false" :before-upload="onAvatarUpload" accept="image/*">
            <el-avatar :size="64" :src="form.avatar ? '/uploads/' + form.avatar : ''">
              <el-icon><Plus /></el-icon>
            </el-avatar>
          </el-upload>
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!form.id" />
        </el-form-item>
        <el-form-item v-if="!form.id" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="昵称"><el-input v-model="form.nickname" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_ids" multiple style="width:100%;" placeholder="选择角色">
            <el-option v-for="r in allRoles" :key="r.id" :label="r.role_name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
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
import { userApi, roleApi, profileApi } from '@/api'

const query = reactive({ page: 1, pageSize: 10, keyword: '', status: '' })
const list = ref([]); const total = ref(0); const loading = ref(false)
const dialogVisible = ref(false); const formRef = ref(); const allRoles = ref([])
const form = reactive({ id: null, username: '', password: '', nickname: '', email: '', phone: '', avatar: '', role_ids: [], status: 1 })
const rules = {
  username: [{ required: true, message: '请输入用户名' }, { min: 3, max: 20 }],
  password: [{ required: true, message: '请输入密码' }, { min: 6 }]
}

async function loadData(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const params = { ...query }
    if (params.status === '' || params.status === null) delete params.status
    if (!params.keyword) delete params.keyword
    const res = await userApi.page(params)
    list.value = res.data.list; total.value = res.data.total
  } finally { loading.value = false }
}
function onReset() { query.keyword = ''; query.status = ''; loadData(1) }

async function loadRoles() {
  const res = await roleApi.all()
  allRoles.value = res.data
}

function onAdd() {
  Object.assign(form, { id: null, username: '', password: '', nickname: '', email: '', phone: '', avatar: '', role_ids: [], status: 1 })
  dialogVisible.value = true
}

function onEdit(row) {
  Object.assign(form, { ...row, password: '', role_ids: row.role_ids || [] })
  dialogVisible.value = true
}

async function onAvatarUpload(file) {
  const r = await profileApi.uploadAvatar(file)
  form.avatar = r.data.path
  ElMessage.success('上传成功')
  return false
}

async function onSave() {
  await formRef.value.validate()
  if (form.id) await userApi.update(form.id, form)
  else await userApi.add(form)
  ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
}

async function onResetPwd(row) {
  await ElMessageBox.confirm(`确认重置 [${row.username}] 的密码为 123456？`, '提示', { type: 'warning' })
  await userApi.resetPwd(row.id); ElMessage.success('密码已重置为 123456')
}

async function onDel(id) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await userApi.del(id); ElMessage.success('已删除'); loadData()
}

onMounted(() => { loadData(); loadRoles() })
</script>
