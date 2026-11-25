<template>
  <!-- 没有子项 -->
  <el-menu-item v-if="!hasChildren" :index="item.path">
    <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
    <template #title>{{ item.name }}</template>
  </el-menu-item>

  <!-- 有子项 -->
  <el-sub-menu v-else :index="item.path">
    <template #title>
      <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
      <span>{{ item.name }}</span>
    </template>
    <SidebarItem v-for="c in item.children" :key="c.id" :item="c" />
  </el-sub-menu>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ item: Object })
const hasChildren = computed(() => props.item.children && props.item.children.length > 0)
</script>
