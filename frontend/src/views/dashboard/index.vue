<template>
  <component :is="dashCmp" />
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const Admin = defineAsyncComponent(() => import('./Admin.vue'))
const Security = defineAsyncComponent(() => import('./Security.vue'))
const UserDash = defineAsyncComponent(() => import('./User.vue'))

const dashCmp = computed(() => {
  const roles = userStore.roles || []
  if (roles.includes('admin')) return Admin
  if (roles.includes('security')) return Security
  return UserDash
})
</script>
