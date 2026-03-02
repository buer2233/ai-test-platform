<!--
  应用根组件
  - 作为 Vue Router 的顶层容器，通过 <router-view /> 渲染当前路由对应的页面组件
  - 全局样式仅设置字体、文字颜色和最小视口高度
-->
<template>
  <router-view />
</template>

<style>
/* 应用根节点全局样式 */
#app {
  font-family: var(--font-family-body);
  color: var(--color-text-primary);
  min-height: 100vh;
}
</style>
