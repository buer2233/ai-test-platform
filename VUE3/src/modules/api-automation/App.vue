<!--
  App.vue - 应用根组件

  使用 Element Plus 的 ElConfigProvider 包裹路由出口，
  提供全局 UI 框架配置。同时定义全局样式，包括：
  - 基础重置样式（html/body/app）
  - 自定义滚动条样式
  - 全局过渡动画
  - 页面通用布局样式
  - 表格工具栏通用样式
-->
<template>
  <el-config-provider>
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import { ElConfigProvider } from 'element-plus'
</script>

<style>
/* ==================== 基础重置 ==================== */

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  height: 100%;
}

/* ==================== 自定义滚动条 ==================== */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* ==================== 全局过渡动画 ==================== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ==================== 页面通用布局 ==================== */
.page-container {
  padding: 20px;
  background: #f5f5f5;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.page-description {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

/* ==================== 工具类 ==================== */
.mb-20 {
  margin-bottom: 20px;
}

/* ==================== 表格工具栏 ==================== */
.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.table-toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.table-toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
