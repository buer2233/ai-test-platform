<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
</script>

<style>
#app {
  font-family: var(--font-family-body);
  color: var(--color-text-primary);
  min-height: 100vh;
}
</style>
