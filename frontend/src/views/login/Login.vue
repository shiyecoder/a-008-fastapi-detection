<template>
  <div class="auth-shell" :style="{ backgroundImage: `url(${bgImg})` }">
    <!-- 顶部状态栏 -->
    <header class="top-bar">
      <div class="brand-mini">
        <span class="logo-dot"></span>
        <span class="brand-name">WEBSHELL · DETECTION PLATFORM</span>
      </div>
      <div class="status">
        <span class="dot live"></span>
        <span>SYSTEM ONLINE</span>
        <span class="sep">|</span>
        <span>{{ now }}</span>
      </div>
    </header>

    <!-- 中心卡片 -->
    <main class="auth-main">
      <div class="auth-card">
        <div class="card-head">
          <div class="head-left">
            <div class="emblem">
              <el-icon :size="22" color="#67c9ff"><Lock /></el-icon>
            </div>
            <div>
              <h1>欢迎回来</h1>
              <p class="sub">Webshell 检测与响应平台 · 安全管控控制台</p>
            </div>
          </div>
          <div class="head-right">v1.0</div>
        </div>

        <div class="meta-strip">
          <div class="meta-item"><span class="num">8</span><span>检测引擎</span></div>
          <div class="meta-item"><span class="num">99.6%</span><span>识别准确率</span></div>
          <div class="meta-item"><span class="num">24/7</span><span>实时监控</span></div>
        </div>

        <el-form :model="form" :rules="rules" ref="formRef" size="large" @keyup.enter="onLogin" class="auth-form">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="请输入账号" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" :prefix-icon="Lock" show-password />
          </el-form-item>

          <div class="row-helper">
            <el-checkbox v-model="remember">记住账号</el-checkbox>
            <span class="weak">忘记密码请联系管理员</span>
          </div>

          <el-button type="primary" :loading="loading" @click="onLogin" class="primary-btn">
            <span>进入控制台</span>
            <el-icon style="margin-left:6px"><Right /></el-icon>
          </el-button>
        </el-form>

        <div class="card-foot">
          <span>还没有账号？</span>
          <router-link to="/register">立即注册 →</router-link>
        </div>
      </div>
    </main>

    <!-- 底部 -->
    <footer class="bottom-bar">
      <span>© 2026 Webshell Detection Platform</span>
      <span class="dim">Secured by YARA · Sandbox · Static Engine</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Right } from '@element-plus/icons-vue'
import { authApi } from '@/api'
import { useUserStore } from '@/store/user'
import bgImg from '@/assets/login-bg.svg'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const remember = ref(true)
const form = reactive({ username: 'admin', password: '123456' })
const rules = {
  username: [{ required: true, message: '请输入用户名' }],
  password: [{ required: true, message: '请输入密码' }]
}

const now = ref('')
let timer = null
function tick() {
  const d = new Date()
  const pad = n => String(n).padStart(2, '0')
  now.value = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
onMounted(() => { tick(); timer = setInterval(tick, 1000) })
onBeforeUnmount(() => { if (timer) clearInterval(timer) })

async function onLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    const res = await authApi.login(form)
    userStore.setToken(res.data.token)
    await userStore.loadInfo()
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-shell {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  background-color: #051428;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  display: flex;
  flex-direction: column;
  color: #cfe2ff;
  overflow: hidden;
}

.top-bar {
  height: 52px;
  padding: 0 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(103, 201, 255, 0.12);
  background: rgba(5, 20, 40, 0.45);
  backdrop-filter: blur(8px);
  font-family: Consolas, 'Courier New', monospace;
  font-size: 12px;
  letter-spacing: 1.4px;
}
.brand-mini { display: flex; align-items: center; gap: 10px; }
.logo-dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: #67c9ff;
  box-shadow: 0 0 10px #67c9ff;
}
.brand-name { color: #67c9ff; font-weight: 600; }
.status { display: flex; align-items: center; gap: 10px; opacity: 0.85; }
.status .dot {
  width: 8px; height: 8px; border-radius: 50%; display: inline-block;
}
.status .dot.live { background: #5ce6a6; box-shadow: 0 0 8px #5ce6a6; animation: blink 1.6s infinite; }
.status .sep { opacity: 0.4; }
@keyframes blink { 50% { opacity: 0.3; } }

.auth-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.auth-card {
  width: 440px;
  background: linear-gradient(160deg, rgba(13, 36, 68, 0.82) 0%, rgba(8, 22, 44, 0.82) 100%);
  border: 1px solid rgba(103, 201, 255, 0.18);
  border-radius: 14px;
  padding: 32px 36px 28px;
  backdrop-filter: blur(14px);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  position: relative;
  overflow: hidden;
}
.auth-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, #67c9ff 50%, transparent 100%);
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}
.head-left { display: flex; gap: 14px; align-items: center; }
.emblem {
  width: 44px; height: 44px;
  border-radius: 10px;
  background: rgba(103, 201, 255, 0.12);
  border: 1px solid rgba(103, 201, 255, 0.35);
  display: flex; align-items: center; justify-content: center;
}
.card-head h1 {
  margin: 0; font-size: 20px; color: #fff; font-weight: 600;
  letter-spacing: 1px;
}
.card-head .sub {
  margin: 4px 0 0; font-size: 12px; color: #8aa6c8;
  letter-spacing: 0.4px;
}
.head-right {
  font-family: Consolas, monospace;
  font-size: 11px;
  color: #67c9ff;
  border: 1px solid rgba(103, 201, 255, 0.4);
  padding: 2px 8px;
  border-radius: 4px;
}

.meta-strip {
  display: flex;
  justify-content: space-between;
  padding: 14px 4px;
  border-top: 1px dashed rgba(103, 201, 255, 0.18);
  border-bottom: 1px dashed rgba(103, 201, 255, 0.18);
  margin-bottom: 22px;
}
.meta-item {
  display: flex; flex-direction: column; gap: 2px;
  font-size: 11px; color: #8aa6c8; text-align: center; flex: 1;
}
.meta-item .num {
  font-family: Consolas, monospace;
  color: #67c9ff;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 1px;
}

.auth-form :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(103, 201, 255, 0.18);
  box-shadow: none !important;
  height: 44px;
}
.auth-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(103, 201, 255, 0.4);
}
.auth-form :deep(.el-input__wrapper.is-focus) {
  border-color: #67c9ff;
  box-shadow: 0 0 0 1px rgba(103, 201, 255, 0.25) !important;
}
.auth-form :deep(.el-input__inner) {
  color: #e8f1ff;
}
.auth-form :deep(.el-input__inner::placeholder) {
  color: #6b86a7;
}
.auth-form :deep(.el-input__prefix-inner > .el-icon) {
  color: #67c9ff;
}

.row-helper {
  display: flex; justify-content: space-between; align-items: center;
  margin: -6px 0 14px;
  font-size: 12px;
}
.row-helper :deep(.el-checkbox__label) { color: #8aa6c8; font-size: 12px; }
.weak { color: #6b86a7; }

.primary-btn {
  width: 100%;
  height: 46px;
  background: linear-gradient(90deg, #1a3a5f 0%, #2c5282 50%, #1e6cb8 100%);
  border: 1px solid rgba(103, 201, 255, 0.5);
  font-size: 14px;
  letter-spacing: 4px;
  font-weight: 500;
}
.primary-btn:hover {
  background: linear-gradient(90deg, #2c5282 0%, #1e6cb8 50%, #2a8fd8 100%);
  box-shadow: 0 6px 20px rgba(46, 115, 195, 0.35);
}

.card-foot {
  margin-top: 18px;
  text-align: center;
  font-size: 12px;
  color: #8aa6c8;
}
.card-foot a {
  color: #67c9ff;
  margin-left: 6px;
  text-decoration: none;
}
.card-foot a:hover { text-shadow: 0 0 6px rgba(103, 201, 255, 0.5); }

.bottom-bar {
  height: 36px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  font-size: 11px;
  color: #5d7896;
  font-family: Consolas, monospace;
  letter-spacing: 0.6px;
  border-top: 1px solid rgba(103, 201, 255, 0.08);
  background: rgba(5, 20, 40, 0.4);
}
.bottom-bar .dim { opacity: 0.7; }
</style>
