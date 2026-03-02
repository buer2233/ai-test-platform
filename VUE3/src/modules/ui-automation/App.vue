<template>
  <!-- UI自动化测试模块根组件：作为模块入口，渲染路由匹配的子视图 -->
  <router-view />
</template>

<script setup lang="ts">
/**
 * UI自动化测试模块根组件
 *
 * 职责：
 * - 作为 ui-automation 模块的顶层容器
 * - 通过 <router-view /> 渲染当前路由对应的页面组件
 * - 模块级布局由 UiLayout 组件负责（在路由配置中指定）
 */
</script>

<style scoped>
/* 模块级别样式（预留，当前无全局样式需求） */
</style>
