<template>
  <div class="app-sidebar">
    <div class="sidebar-scroll">
      <!-- Primary Navigation Group -->
      <div class="nav-group">
        <ul class="nav-list">
          <li v-for="item in primaryNav" :key="item.href" class="nav-item">
            <a
              :href="item.href"
              class="nav-link"
              :class="{ 'is-active': modelValue === item.href }"
            >
              <span class="nav-icon" v-html="item.icon"></span>
              <span class="nav-label">{{ item.label }}</span>
            </a>
          </li>
        </ul>
      </div>

      <!-- 文档库 Section -->
      <div class="nav-group nav-group--spaced">
        <div class="section-label">文档库</div>
        <ul class="nav-list">
          <li v-for="item in docsNav" :key="item.href" class="nav-item">
            <a
              :href="item.href"
              target="_blank"
              rel="noopener noreferrer"
              class="nav-link"
              :class="{ 'is-active': modelValue === item.href }"
            >
              <span class="nav-icon" v-html="item.icon"></span>
              <span class="nav-label nav-label--flex">{{ item.label }}</span>
              <span class="nav-external" v-html="iconExternalLink"></span>
            </a>
          </li>
        </ul>
      </div>

      <!-- 服务 Section -->
      <div class="nav-group nav-group--spaced">
        <div class="section-label">服务</div>
        <ul class="nav-list">
          <li v-for="item in serviceNav" :key="item.href" class="nav-item">
            <a
              :href="item.href"
              class="nav-link"
              :class="{ 'is-active': modelValue === item.href }"
            >
              <span class="nav-icon" v-html="item.icon"></span>
              <span class="nav-label">{{ item.label }}</span>
            </a>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ modelValue?: string }>(), { modelValue: '/trade' })

const iconHouse = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/>
  <path d="M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
</svg>`

const iconStore = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M15 21v-5a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v5"/>
  <path d="M17.774 10.31a1.12 1.12 0 0 0-1.549 0 2.5 2.5 0 0 1-3.451 0 1.12 1.12 0 0 0-1.548 0 2.5 2.5 0 0 1-3.452 0 1.12 1.12 0 0 0-1.549 0 2.5 2.5 0 0 1-3.77-3.248l2.889-4.184A2 2 0 0 1 7 2h10a2 2 0 0 1 1.653.873l2.895 4.192a2.5 2.5 0 0 1-3.774 3.244"/>
  <path d="M4 10.95V19a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8.05"/>
</svg>`

const iconWallet = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/>
  <path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>
</svg>`

const iconCircleDollar = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <circle cx="12" cy="12" r="10"/>
  <path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/>
  <path d="M12 18V6"/>
</svg>`

const iconTrophy = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M10 14.66v1.626a2 2 0 0 1-.976 1.696A5 5 0 0 0 7 21.978"/>
  <path d="M14 14.66v1.626a2 2 0 0 0 .976 1.696A5 5 0 0 1 17 21.978"/>
  <path d="M18 9h1.5a1 1 0 0 0 0-5H18"/>
  <path d="M4 22h16"/>
  <path d="M6 9a6 6 0 0 0 12 0V3a1 1 0 0 0-1-1H7a1 1 0 0 0-1 1z"/>
  <path d="M6 9H4.5a1 1 0 0 1 0-5H6"/>
</svg>`

const iconCreditCard = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <rect width="20" height="14" x="2" y="5" rx="2"/>
  <line x1="2" x2="22" y1="10" y2="10"/>
</svg>`

const iconFileText = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"/>
  <path d="M14 2v5a1 1 0 0 0 1 1h5"/>
  <path d="M10 9H8"/>
  <path d="M16 13H8"/>
  <path d="M16 17H8"/>
</svg>`

const iconGlobe = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <circle cx="12" cy="12" r="10"/>
  <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>
  <path d="M2 12h20"/>
</svg>`

const iconExternalLink = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M7 7h10v10"/>
  <path d="M7 17 17 7"/>
</svg>`

const primaryNav = [
  { href: '/home',        label: '首页',   icon: iconHouse },
  { href: '/merchant',    label: '集市',   icon: iconStore },
  { href: '/balance',     label: '积分',   icon: iconWallet },
  { href: '/trade',       label: '活动',   icon: iconCircleDollar },
  { href: '/leaderboard', label: '排行榜', icon: iconTrophy },
]

const docsNav = [
  { href: '/docs/api',          label: '接口文档', icon: iconCreditCard },
  { href: '/docs/how-to-use',   label: '使用文档', icon: iconFileText },
]

const serviceNav = [
  { href: '/merchant/online-paying', label: '在线流转', icon: iconGlobe },
]
</script>

<style scoped>
.app-sidebar {
  width: 223px;
  height: 100%;
  background: #ffffff;
  font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  line-height: 20px;
  color: rgb(63, 63, 70);
  overflow: hidden;
  flex-shrink: 0;
}

.sidebar-scroll {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0 8px;
  box-sizing: border-box;
}

.sidebar-scroll::-webkit-scrollbar {
  width: 4px;
}
.sidebar-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.sidebar-scroll::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
}
.sidebar-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}

/* Groups */
.nav-group {
  width: 100%;
}

.nav-group--spaced {
  padding-top: 16px;
}

/* Section label */
.section-label {
  display: flex;
  align-items: center;
  height: 32px;
  padding: 0 8px;
  font-size: 12px;
  line-height: 16px;
  color: #71717a;
  font-weight: 400;
  user-select: none;
}

/* Nav list */
.nav-list {
  list-style: none;
  margin: 0;
  padding: 4px 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  width: 100%;
}

/* Nav link */
.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  height: 32px;
  padding: 8px;
  box-sizing: border-box;
  border-radius: 8px;
  text-decoration: none;
  color: rgb(63, 63, 70);
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
  cursor: pointer;
  overflow: hidden;
  transition:
    background-color 0.15s cubic-bezier(0.4, 0, 0.2, 1),
    color 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.nav-link:hover {
  background-color: #f4f4f5;
  color: rgb(63, 63, 70);
}

.nav-link.is-active {
  color: #6366f1;
  font-weight: 700;
}

.nav-link.is-active:hover {
  background-color: #f4f4f5;
  color: #6366f1;
}

/* Icon */
.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 16px;
  height: 16px;
}

.nav-icon :deep(svg) {
  display: block;
}

/* Label */
.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-label--flex {
  flex: 1;
  min-width: 0;
}

/* External link icon */
.nav-external {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  color: #71717a;
  margin-left: auto;
}

.nav-external :deep(svg) {
  display: block;
}
</style>
