/**
 * 路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

// 静态路由
const routes = [
  { path: '/login', component: () => import('@/views/login/Login.vue'), meta: { hidden: true } },
  { path: '/register', component: () => import('@/views/register/Register.vue'), meta: { hidden: true } },
  {
    path: '/',
    component: () => import('@/layout/Index.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', component: () => import('@/views/dashboard/index.vue'), meta: { title: '工作台' } },

      { path: 'detection/scan', component: () => import('@/views/detection/Scan.vue'), meta: { title: '静态/动态检测' } },
      { path: 'detection/list', component: () => import('@/views/detection/List.vue'), meta: { title: '检测任务' } },
      { path: 'detection/yara', component: () => import('@/views/detection/Yara.vue'), meta: { title: 'YARA规则' } },
      { path: 'detection/signature', component: () => import('@/views/detection/Signature.vue'), meta: { title: '签名规则库' } },
      { path: 'detection/hash', component: () => import('@/views/detection/HashLib.vue'), meta: { title: '哈希黑名单' } },
      { path: 'detection/quarantine', component: () => import('@/views/detection/Quarantine.vue'), meta: { title: '隔离区' } },

      { path: 'alert/list', component: () => import('@/views/alert/List.vue'), meta: { title: '告警中心' } },
      { path: 'alert/vuln-fix', component: () => import('@/views/alert/VulnFix.vue'), meta: { title: '漏洞修复库' } },

      { path: 'report/list', component: () => import('@/views/report/List.vue'), meta: { title: '报告管理' } },

      { path: 'system/user', component: () => import('@/views/system/User.vue'), meta: { title: '用户管理' } },
      { path: 'system/role', component: () => import('@/views/system/Role.vue'), meta: { title: '角色管理' } },
      { path: 'system/menu', component: () => import('@/views/system/Menu.vue'), meta: { title: '菜单管理' } },
      { path: 'system/log', component: () => import('@/views/system/Log.vue'), meta: { title: '操作日志' } },

      { path: 'profile', component: () => import('@/views/profile/Index.vue'), meta: { title: '个人中心' } }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  if (to.path === '/login' || to.path === '/register') return next()
  if (!userStore.token) return next('/login')
  if (!userStore.username) {
    try {
      await userStore.loadInfo()
    } catch (e) {
      userStore.logout()
      return next('/login')
    }
  }
  next()
})

export default router
