<template>
  <div class="profile-page">
    <el-tabs v-model="tab">
      <el-tab-pane label="基本资料" name="info">
        <div class="app-card" style="max-width:600px;">
          <el-form :model="info" label-width="100px">
            <el-form-item label="头像">
              <el-upload :show-file-list="false" :before-upload="onAvatarUpload" accept="image/*">
                <el-avatar :size="80" :src="info.avatar ? '/uploads/' + info.avatar : ''">
                  <el-icon><Plus /></el-icon>
                </el-avatar>
              </el-upload>
              <div style="font-size:12px;color:#909399;margin-top:6px;">点击头像上传新图片</div>
            </el-form-item>
            <el-form-item label="用户名"><el-input v-model="info.username" disabled /></el-form-item>
            <el-form-item label="昵称"><el-input v-model="info.nickname" /></el-form-item>
            <el-form-item label="邮箱"><el-input v-model="info.email" /></el-form-item>
            <el-form-item label="手机号"><el-input v-model="info.phone" /></el-form-item>
            <el-form-item>
              <el-button type="primary" @click="onSaveInfo">保存修改</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>
      <el-tab-pane label="修改密码" name="password">
        <div class="app-card" style="max-width:500px;">
          <el-form :model="pwd" :rules="pwdRules" ref="pwdRef" label-width="120px">
            <el-form-item label="原密码" prop="old_password">
              <el-input v-model="pwd.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="pwd.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirm">
              <el-input v-model="pwd.confirm" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="onSavePwd">保存修改</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { profileApi } from '@/api'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const tab = ref('info')
const info = reactive({ username: '', nickname: '', email: '', phone: '', avatar: '' })
const pwdRef = ref()
const pwd = reactive({ old_password: '', new_password: '', confirm: '' })
const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码' }],
  new_password: [{ required: true, min: 6, message: '至少6位' }],
  confirm: [{ required: true, validator: (_, v, cb) => v !== pwd.new_password ? cb(new Error('两次密码不一致')) : cb() }]
}

function loadInfo() {
  info.username = userStore.username
  info.nickname = userStore.nickname
  info.email = userStore.email
  info.phone = userStore.phone
  info.avatar = userStore.avatar
}

async function onAvatarUpload(file) {
  const r = await profileApi.uploadAvatar(file)
  // 后端返回 { avatar: 'avatars/2026-05-15/xxx.png' }，并已写入用户表
  const path = r.data.avatar || r.data.path
  info.avatar = path
  userStore.setAvatar(path)
  ElMessage.success('头像上传成功')
  return false
}

async function onSaveInfo() {
  await profileApi.update({ nickname: info.nickname, email: info.email, phone: info.phone, avatar: info.avatar })
  userStore.setProfile({ nickname: info.nickname, email: info.email, phone: info.phone })
  ElMessage.success('保存成功')
}

async function onSavePwd() {
  await pwdRef.value.validate()
  await profileApi.password({ old_password: pwd.old_password, new_password: pwd.new_password })
  ElMessage.success('密码修改成功，请重新登录')
  userStore.logout()
  setTimeout(() => location.href = '/login', 800)
}

onMounted(loadInfo)
</script>

<style scoped>
.profile-page { background: #fff; padding: 16px; border-radius: 6px; min-height: 100%; }
</style>
