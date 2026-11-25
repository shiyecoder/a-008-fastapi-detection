<template>
  <el-container class="layout">
    <el-aside :width="collapse ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <el-icon size="24" color="#fff"><Lock /></el-icon>
        <span v-if="!collapse">Webshell检测平台</span>
      </div>
      <el-scrollbar>
        <el-menu
          :default-active="activeMenu"
          background-color="#1a3a5f"
          text-color="#cbd5e0"
          active-text-color="#fff"
          :collapse="collapse"
          :collapse-transition="false"
          router
        >
          <SidebarItem v-for="m in visibleMenus" :key="m.id" :item="m" />
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon @click="collapse = !collapse" style="cursor:pointer;font-size:20px;">
            <Fold v-if="!collapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/" style="margin-left:16px;">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="onCmd">
            <span class="user-info">
              <el-avatar :size="32" :src="avatarUrl">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span style="margin-left:8px;">{{ userStore.nickname || userStore.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import SidebarItem from './SidebarItem.vue'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const collapse = ref(false)

const activeMenu = computed(() => route.path)

// 过滤菜单：仅显示visible=1
function filterTree(arr) {
  if (!arr) return []
  return arr.filter(m => m.visible === 1).map(m => ({
    ...m, children: filterTree(m.children)
  }))
}
const visibleMenus = computed(() => filterTree(userStore.menus))

const avatarUrl = computed(() => userStore.avatar ? `/uploads/${userStore.avatar}` : '')

function onCmd(cmd) {
  if (cmd === 'profile') router.push('/profile')
  else if (cmd === 'logout') {
    ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' }).then(() => {
      userStore.logout()
      router.push('/login')
    })
  }
}
</script>

<style lang="scss" scoped>
.layout { height: 100vh; }

.sidebar {
  background: #1a3a5f;
  transition: width 0.2s;
  overflow: hidden;
}

.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #fff;
  font-weight: 600;
  font-size: 15px;
  background: #14304d;
  white-space: nowrap;
}

.header {
  height: 56px !important;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  z-index: 5;
}
.header-left { display: flex; align-items: center; }
.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  outline: none;
}

.main { background: #f4f6f9; padding: 16px; overflow-y: auto; }

:deep(.el-menu) { border-right: none; }
:deep(.el-menu--collapse) { width: 64px; }
</style>
