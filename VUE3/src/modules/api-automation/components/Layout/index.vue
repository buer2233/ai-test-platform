<template>
  <div class="layout-container">
    <!-- Sidebar -->
    <aside data-testid="main-sidebar" :class="['layout-sidebar', { 'is-collapsed': isCollapse }]">
      <!-- Logo Section with Module Switcher -->
      <div class="sidebar-logo" data-testid="module-switcher" @click="toggleModuleDropdown">
        <div class="logo-icon" :class="{ 'is-ui': currentPlatform === 'ui' }">
          <svg v-if="currentPlatform === 'api'" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M32 8L56 20V44L32 56L8 44V20L32 8Z" stroke="url(#sidebar-logo-gradient)" stroke-width="2" fill="none"/>
            <path d="M32 24V40M24 32H40" stroke="url(#sidebar-logo-gradient)" stroke-width="2" stroke-linecap="round"/>
            <circle cx="32" cy="32" r="4" fill="url(#sidebar-logo-gradient)"/>
            <defs>
              <linearGradient id="sidebar-logo-gradient" x1="8" y1="8" x2="56" y2="56">
                <stop stop-color="#4F7FFF"/>
                <stop offset="1" stop-color="#7CA0FF"/>
              </linearGradient>
            </defs>
          </svg>
          <svg v-else viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="8" y="8" width="48" height="48" rx="8" stroke="url(#ui-logo-gradient)" stroke-width="2" fill="none"/>
            <path d="M20 32L28 40L44 24" stroke="url(#ui-logo-gradient)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="32" cy="32" r="14" stroke="url(#ui-logo-gradient)" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.6"/>
            <defs>
              <linearGradient id="ui-logo-gradient" x1="8" y1="8" x2="56" y2="56">
                <stop stop-color="#4F7FFF"/>
                <stop offset="1" stop-color="#7CA0FF"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div v-show="!isCollapse" class="logo-text">
          <span class="logo-title">{{ currentPlatform === 'api' ? 'API 测试平台' : 'AI 驱动 UI 测试' }}</span>
          <span class="logo-subtitle">{{ currentPlatform === 'api' ? 'AUTOMATION' : 'INTELLIGENT' }}</span>
        </div>
        <el-icon v-show="!isCollapse" class="dropdown-arrow" :class="{ 'is-open': showModuleDropdown }">
          <ArrowDown />
        </el-icon>

        <!-- Module Dropdown Menu -->
        <transition name="dropdown-fade">
          <div v-show="showModuleDropdown" class="module-dropdown" @click.stop>
            <div class="module-dropdown-item" :class="{ 'is-active': currentPlatform === 'ui' }" @click="switchToUiPlatform">
              <div class="module-item-icon ui-icon">
                <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="8" y="8" width="48" height="48" rx="8" stroke="currentColor" stroke-width="2" fill="none"/>
                  <path d="M20 32L28 40L44 24" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="32" cy="32" r="14" stroke="currentColor" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.6"/>
                </svg>
              </div>
              <div class="module-item-info">
                <span class="module-item-title">AI 驱动 UI 测试</span>
                <span class="module-item-desc">智能浏览器自动化测试</span>
              </div>
            </div>
            <div class="module-dropdown-item" :class="{ 'is-active': currentPlatform === 'api' }" @click="switchToApiPlatform">
              <div class="module-item-icon api-icon">
                <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M32 8L56 20V44L32 56L8 44V20L32 8Z" stroke="currentColor" stroke-width="2" fill="none"/>
                  <path d="M32 24V40M24 32H40" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <circle cx="32" cy="32" r="4" fill="currentColor"/>
                </svg>
              </div>
              <div class="module-item-info">
                <span class="module-item-title">API 测试平台</span>
                <span class="module-item-desc">接口自动化测试</span>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Navigation Menu -->
      <nav class="sidebar-nav">
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :unique-opened="true"
          router
          class="nav-menu"
        >
          <el-menu-item index="/dashboard" class="nav-item">
            <el-icon><Odometer /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>

          <el-menu-item index="/projects" class="nav-item">
            <el-icon><FolderOpened /></el-icon>
            <template #title>项目管理</template>
          </el-menu-item>

          <el-menu-item index="/collections" class="nav-item">
            <el-icon><Collection /></el-icon>
            <template #title>集合管理</template>
          </el-menu-item>

          <el-menu-item index="/test-cases" class="nav-item">
            <el-icon><DocumentChecked /></el-icon>
            <template #title>测试用例</template>
          </el-menu-item>

          <el-menu-item index="/environments" class="nav-item">
            <el-icon><Setting /></el-icon>
            <template #title>环境管理</template>
          </el-menu-item>

          <div class="nav-divider"></div>

          <el-menu-item index="/http-executor" class="nav-item nav-item-accent">
            <el-icon><Lightning /></el-icon>
            <template #title>HTTP 执行器</template>
          </el-menu-item>

          <el-menu-item index="/reports" class="nav-item">
            <el-icon><Document /></el-icon>
            <template #title>测试报告</template>
          </el-menu-item>

          <el-menu-item index="/recycle-bin" class="nav-item">
            <el-icon><Delete /></el-icon>
            <template #title>回收站</template>
          </el-menu-item>
        </el-menu>
      </nav>

      <!-- Sidebar Footer -->
      <div class="sidebar-footer">
        <div class="status-indicator">
          <span class="status-dot"></span>
          <span v-show="!isCollapse" class="status-text">系统正常</span>
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="layout-main">
      <!-- Header -->
      <header class="layout-header" data-testid="main-header">
        <div class="header-left">
          <button class="header-btn collapse-btn" @click="toggleCollapse">
            <el-icon>
              <Expand v-if="isCollapse" />
              <Fold v-else />
            </el-icon>
          </button>

          <el-breadcrumb separator="/" class="header-breadcrumb">
            <el-breadcrumb-item
              v-for="item in breadcrumbList"
              :key="item.path"
              :to="item.path"
            >
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <div class="header-actions">
            <button class="header-btn" title="快速执行">
              <el-icon><Lightning /></el-icon>
            </button>
            <button class="header-btn" title="通知">
              <el-icon><Bell /></el-icon>
            </button>
            <button class="header-btn" title="设置">
              <el-icon><Setting /></el-icon>
            </button>
          </div>

          <el-dropdown @command="handleCommand" trigger="click">
            <div class="user-dropdown">
              <el-avatar :size="36" :icon="UserFilled" class="user-avatar" />
              <span v-show="!isHeaderCompact" class="user-name">
                {{ currentUser?.username || '用户' }}
              </span>
              <el-icon class="dropdown-arrow">
                <ArrowDown />
              </el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- Page Content -->
      <main class="layout-content">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  Odometer,
  FolderOpened,
  Collection,
  DocumentChecked,
  Setting,
  Expand,
  Fold,
  UserFilled,
  ArrowDown,
  User,
  SwitchButton,
  Lightning,
  Bell,
  Document,
  Delete,
  Monitor
} from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isCollapse = ref(false)
const isHeaderCompact = ref(false)
const currentPlatform = ref<'api' | 'ui'>('api')
const showModuleDropdown = ref(false)

const currentUser = computed(() => authStore.user)
const activeMenu = computed(() => route.path)

// 切换模块下拉菜单
const toggleModuleDropdown = () => {
  showModuleDropdown.value = !showModuleDropdown.value
}

// 切换到API测试平台
const switchToApiPlatform = () => {
  currentPlatform.value = 'api'
  showModuleDropdown.value = false
  router.push('/dashboard')
}

// 切换到UI自动化平台
const switchToUiPlatform = () => {
  currentPlatform.value = 'ui'
  showModuleDropdown.value = false
  router.push('/ui-automation/projects')
}

const breadcrumbList = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  return matched.map(item => ({
    path: item.path,
    title: item.meta.title as string
  }))
})

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const handleCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      break
    case 'settings':
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await authStore.logout()
        router.push('/login')
      } catch {
        // User cancelled
      }
      break
  }
}

const handleResize = () => {
  isHeaderCompact.value = window.innerWidth < 1200
  if (window.innerWidth < 768) {
    isCollapse.value = true
  }
}

// 点击外部关闭下拉菜单
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement
  // 检查点击是否在logo区域或下拉菜单内
  if (target.closest('.sidebar-logo')) {
    return
  }
  showModuleDropdown.value = false
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* LAYOUT CONTAINER */
.layout-container {
  display: flex;
  min-height: 100vh;
  background-color: var(--color-bg-primary);
}

/* SIDEBAR */
.layout-sidebar {
  width: 260px;
  min-height: 100vh;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border-primary);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  position: relative;
  z-index: 100;
}

.layout-sidebar::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 1px;
  background: linear-gradient(180deg, transparent 0%, var(--color-accent-primary) 50%, transparent 100%);
  opacity: 0.3;
}

.layout-sidebar.is-collapsed {
  width: 70px;
}

/* LOGO with Module Switcher */
.sidebar-logo {
  height: 70px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid var(--color-border-secondary);
  position: relative;
  gap: 12px;
  cursor: pointer;
  user-select: none;
}

.sidebar-logo::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 20px;
  right: 20px;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, var(--color-accent-primary) 50%, transparent 100%);
  opacity: 0.5;
}

.logo-icon svg {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}

.logo-icon.is-ui svg {
  filter: drop-shadow(0 0 8px rgba(79, 127, 255, 0.35));
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: 0.025em;
}

.logo-subtitle {
  font-size: 10px;
  font-family: var(--font-family-mono);
  color: var(--color-accent-primary);
  letter-spacing: 0.05em;
}

.sidebar-logo .dropdown-arrow {
  margin-left: auto;
  font-size: 12px;
  color: var(--color-text-tertiary);
  transition: transform 0.3s ease;
}

.sidebar-logo .dropdown-arrow.is-open {
  transform: rotate(180deg);
}

/* Module Dropdown */
.module-dropdown {
  position: absolute;
  top: 70px;
  left: 0;
  right: 0;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-primary);
  border-radius: 0 0 8px 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  z-index: 200;
}

.module-dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid var(--color-border-secondary);
}

.module-dropdown-item:last-child {
  border-bottom: none;
}

.module-dropdown-item:hover {
  background: var(--color-bg-tertiary);
}

.module-dropdown-item.is-active {
  background: linear-gradient(90deg, var(--color-accent-muted) 0%, transparent 100%);
  border-left: 3px solid var(--color-accent-primary);
}

.module-item-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.module-item-icon svg {
  width: 24px;
  height: 24px;
}

.module-item-icon.ui-icon svg {
  color: #4F7FFF;
}

.module-item-icon.api-icon svg {
  color: #4F7FFF;
}

.module-item-info {
  display: flex;
  flex-direction: column;
}

.module-item-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.module-item-desc {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: all 0.2s ease;
}

.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* NAVIGATION */
.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-menu {
  background: transparent;
  border: none;
}

.nav-item {
  margin-bottom: 4px;
  border-radius: 6px;
}

.nav-item:hover {
  background: var(--color-bg-tertiary);
}

.nav-item.is-active {
  background: linear-gradient(90deg, var(--color-accent-muted) 0%, transparent 100%);
  border-left: 3px solid var(--color-accent-primary);
}

.nav-item.is-active .el-menu-item__title {
  color: var(--color-accent-primary);
}

.nav-item-accent {
  position: relative;
}

.nav-item-accent::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 6px;
  padding: 1px;
  background: linear-gradient(135deg, var(--color-accent-primary), var(--color-info-primary));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.nav-item-accent:hover::before {
  opacity: 0.5;
}

.nav-divider {
  height: 1px;
  margin: 16px 8px;
  background: linear-gradient(90deg, transparent 0%, var(--color-border-secondary) 50%, transparent 100%);
}

/* FOOTER */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--color-border-secondary);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--color-bg-tertiary);
  border-radius: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-accent-primary);
  animation: status-pulse 2s ease-in-out infinite;
}

@keyframes status-pulse {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 0 0 rgba(79, 127, 255, 0.35);
  }
  50% {
    opacity: 0.7;
    box-shadow: 0 0 0 6px rgba(79, 127, 255, 0);
  }
}

.status-text {
  font-size: 12px;
  font-family: var(--font-family-mono);
  color: var(--color-text-secondary);
}

/* MAIN CONTENT */
.layout-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* HEADER */
.layout-header {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--color-border-primary);
  position: sticky;
  top: 0;
  z-index: 50;
}

.layout-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, var(--color-accent-primary) 50%, transparent 100%);
  opacity: 0.3;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--color-border-secondary);
  border-radius: 6px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.header-btn:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-accent-primary);
  color: var(--color-text-primary);
}

.header-breadcrumb {
  font-size: 14px;
}

.header-breadcrumb :deep(.el-breadcrumb__inner) {
  color: var(--color-text-tertiary);
}

.header-breadcrumb :deep(.el-breadcrumb__inner:hover) {
  color: var(--color-accent-primary);
}

.header-breadcrumb :deep(.el-breadcrumb__separator) {
  color: var(--color-text-tertiary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* USER DROPDOWN */
.user-dropdown {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border-secondary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.user-dropdown:hover {
  border-color: var(--color-accent-primary);
}

.user-avatar {
  background: linear-gradient(135deg, var(--color-accent-primary), var(--color-info-primary));
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.dropdown-arrow {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

/* PAGE CONTENT */
.layout-content {
  flex: 1;
  padding: 24px;
  background: var(--color-bg-primary);
}

/* ANIMATIONS */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: all 0.3s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* RESPONSIVE */
@media (max-width: 768px) {
  .layout-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    transform: translateX(-100%);
  }

  .layout-sidebar.is-collapsed {
    transform: translateX(-100%);
  }

  .layout-sidebar:not(.is-collapsed) {
    transform: translateX(0);
    width: 260px;
  }

  .layout-header {
    padding: 0 16px;
  }

  .header-breadcrumb {
    display: none;
  }
}
</style>


