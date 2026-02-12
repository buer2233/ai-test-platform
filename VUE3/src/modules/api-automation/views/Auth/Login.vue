<template>
  <div class="login-container" data-testid="login-root">
    <!-- Background Effects -->
    <div class="login-bg-grid"></div>
    <div class="login-bg-gradient"></div>
    <div class="login-bg-scanline"></div>

    <!-- Floating Particles -->
    <div class="particles">
      <div v-for="i in 20" :key="i" class="particle" :style="getParticleStyle(i)"></div>
    </div>

    <!-- Auth Card -->
    <div class="auth-card animate-scale-in" data-testid="auth-card">
      <!-- Header -->
      <div class="auth-header">
        <div class="logo-icon">
          <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M32 8L56 20V44L32 56L8 44V20L32 8Z" stroke="url(#logo-gradient)" stroke-width="2" fill="none"/>
            <path d="M32 24V40M24 32H40" stroke="url(#logo-gradient)" stroke-width="2" stroke-linecap="round"/>
            <circle cx="32" cy="32" r="4" fill="url(#logo-gradient)"/>
            <defs>
              <linearGradient id="logo-gradient" x1="8" y1="8" x2="56" y2="56">
                <stop stop-color="#00FF94"/>
                <stop offset="1" stop-color="#00D9FF"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 class="auth-title">API 自动化测试平台</h1>
        <p class="auth-subtitle">Industrial Automation Testing System</p>
      </div>

      <!-- Toggle Tabs -->
      <div class="auth-tabs">
        <button
          data-testid="login-tab" :class="['tab-btn', { active: mode === 'login' }]"
          @click="mode = 'login'"
        >
          登录
        </button>
        <button
          data-testid="register-tab" :class="['tab-btn', { active: mode === 'register' }]"
          @click="mode = 'register'"
        >
          注册
        </button>
        <div class="tab-indicator" :style="{ transform: mode === 'register' ? 'translateX(100%)' : 'translateX(0)' }"></div>
      </div>

      <!-- Login Form -->
      <el-form
        v-show="mode === 'login'"
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="auth-form"
        @submit.prevent="handleLogin"
      >
        <div class="form-group animate-slide-up stagger-1">
          <label class="form-label">
            <span class="label-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 1C9.1 1 10 1.9 10 3V7H6V3C6 1.9 6.9 1 8 1ZM8 9C9.1 9 10 9.9 10 11C10 12.1 9.1 13 8 13C6.9 13 6 12.1 6 11C6 9.9 6.9 9 8 9ZM3 5H13V7H3V5ZM4 8H12V14C12 15.1 11.1 16 10 16H6C4.9 16 4 15.1 4 14V8Z" fill="currentColor"/>
              </svg>
            </span>
            用户名
          </label>
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            clearable
            class="tech-input"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="form-group animate-slide-up stagger-2">
          <label class="form-label">
            <span class="label-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M13 6V5C13 2.8 11.2 1 9 1H7C4.8 1 3 2.8 3 5V6H2V14C2 15.1 2.9 16 4 16H12C13.1 16 14 15.1 14 14V6H13ZM5 5C5 3.9 5.9 3 7 3H9C10.1 3 11 3.9 11 5V6H5V5ZM8 11.5C6.6 11.5 5.5 10.4 5.5 9C5.5 7.6 6.6 6.5 8 6.5C9.4 6.5 10.5 7.6 10.5 9C10.5 10.4 9.4 11.5 8 11.5Z" fill="currentColor"/>
              </svg>
            </span>
            密码
          </label>
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
            clearable
            class="tech-input"
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="form-actions animate-slide-up stagger-3">
          <el-button
            type="primary"
            size="large"
            class="submit-btn" data-testid="login-submit"
            :loading="loading"
            @click="handleLogin"
          >
            <span v-if="!loading">登录系统</span>
            <span v-else>登录中...</span>
          </el-button>
        </div>

        <div class="form-footer animate-slide-up stagger-4">
          <div class="admin-hint">
            <span class="hint-label">管理员账号:</span>
            <span class="hint-value">admin / admin123</span>
          </div>
        </div>
      </el-form>

      <!-- Register Form -->
      <el-form
        v-show="mode === 'register'"
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="auth-form"
        @submit.prevent="handleRegister"
      >
        <div class="form-group animate-slide-up stagger-1">
          <label class="form-label">
            <span class="label-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 1C9.1 1 10 1.9 10 3V7H6V3C6 1.9 6.9 1 8 1ZM8 9C9.1 9 10 9.9 10 11C10 12.1 9.1 13 8 13C6.9 13 6 12.1 6 11C6 9.9 6.9 9 8 9ZM3 5H13V7H3V5ZM4 8H12V14C12 15.1 11.1 16 10 16H6C4.9 16 4 15.1 4 14V8Z" fill="currentColor"/>
              </svg>
            </span>
            用户名
          </label>
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名"
            size="large"
            clearable
            class="tech-input"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="form-group animate-slide-up stagger-2">
          <label class="form-label">
            <span class="label-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M13 6V5C13 2.8 11.2 1 9 1H7C4.8 1 3 2.8 3 5V6H2V14C2 15.1 2.9 16 4 16H12C13.1 16 14 15.1 14 14V6H13ZM5 5C5 3.9 5.9 3 7 3H9C10.1 3 11 3.9 11 5V6H5V5ZM8 11.5C6.6 11.5 5.5 10.4 5.5 9C5.5 7.6 6.6 6.5 8 6.5C9.4 6.5 10.5 7.6 10.5 9C10.5 10.4 9.4 11.5 8 11.5Z" fill="currentColor"/>
              </svg>
            </span>
            密码
          </label>
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码 (至少6位)"
            size="large"
            show-password
            clearable
            class="tech-input"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="form-group animate-slide-up stagger-3">
          <label class="form-label">
            <span class="label-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 0C3.58 0 0 3.58 0 8C0 12.42 3.58 16 8 16C12.42 16 16 12.42 16 8C16 3.58 12.42 0 8 0ZM8 14C4.69 14 2 11.31 2 8C2 4.69 4.69 2 8 2C11.31 2 14 4.69 14 8C14 11.31 11.31 14 8 14ZM8 12C6.9 12 6 11.1 6 10C6 8.9 6.9 8 8 8C7.1 8 8 7.1 8 6C8 4.9 7.1 4 6 4C4.9 4 4 4.9 4 6C4 7.1 4.9 8 6 8C6 9.1 6.9 10 8 10ZM8 4C6.9 4 6 3.1 6 2C6 0.9 6.9 0 8 0C9.1 0 10 0.9 10 2C10 3.1 9.1 4 8 4Z" fill="currentColor"/>
              </svg>
            </span>
            邮箱 (可选)
          </label>
          <el-input
            v-model="registerForm.email"
            placeholder="请输入邮箱"
            size="large"
            clearable
            class="tech-input"
          >
            <template #prefix>
              <el-icon><Message /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="form-group animate-slide-up stagger-4">
          <label class="form-label">
            <span class="label-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M13 6V5C13 2.8 11.2 1 9 1H7C4.8 1 3 2.8 3 5V6H2V14C2 15.1 2.9 16 4 16H12C13.1 16 14 15.1 14 14V6H13ZM5 5C5 3.9 5.9 3 7 3H9C10.1 3 11 3.9 11 5V6H5V5ZM8 11.5C6.6 11.5 5.5 10.4 5.5 9C5.5 7.6 6.6 6.5 8 6.5C9.4 6.5 10.5 7.6 10.5 9C10.5 10.4 9.4 11.5 8 11.5Z" fill="currentColor"/>
              </svg>
            </span>
            确认密码
          </label>
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            size="large"
            show-password
            clearable
            class="tech-input"
            @keyup.enter="handleRegister"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="form-actions animate-slide-up stagger-5">
          <el-button
            type="primary"
            size="large"
            class="submit-btn"
            :loading="loading"
            @click="handleRegister"
          >
            <span v-if="!loading">注册账号</span>
            <span v-else>注册中...</span>
          </el-button>
        </div>
      </el-form>

      <!-- Footer Info -->
      <div class="auth-footer">
        <div class="footer-info">
          <div class="info-item">
            <span class="info-dot"></span>
            <span>系统状态: 在线</span>
          </div>
          <div class="info-item">
            <span class="info-dot warning"></span>
            <span>版本: v2.0.0</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Corner Decorations -->
    <div class="corner corner-tl"></div>
    <div class="corner corner-tr"></div>
    <div class="corner corner-bl"></div>
    <div class="corner corner-br"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores'

const router = useRouter()
const authStore = useAuthStore()

// 登录/注册模式
const mode = ref<'login' | 'register'>('login')

// 表单引用
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

// 加载状态
const loading = ref(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 注册表单数据
const registerForm = reactive({
  username: '',
  password: '',
  email: '',
  confirmPassword: ''
})

// 登录表单验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

// 注册表单验证规则
const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3-20个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
    loading.value = true

    const response = await authStore.login(loginForm.username, loginForm.password)
    authStore.setToken(response.token)
    await authStore.fetchCurrentUser()

    ElMessage.success('登录成功，欢迎回来')
    router.push('/dashboard')
  } catch (error: any) {
    console.error('Login failed:', error)
    ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    await registerFormRef.value.validate()
    loading.value = true

    await authStore.register(
      registerForm.username,
      registerForm.password,
      registerForm.email
    )

    ElMessage.success('注册成功！请使用新账号登录')

    // 切换到登录模式并填充用户名
    mode.value = 'login'
    loginForm.username = registerForm.username
    loginForm.password = ''

    // 重置注册表单
    registerForm.username = ''
    registerForm.password = ''
    registerForm.email = ''
    registerForm.confirmPassword = ''
    registerFormRef.value?.resetFields()
  } catch (error: any) {
    console.error('Register failed:', error)
    ElMessage.error(error.response?.data?.message || '注册失败，请重试')
  } finally {
    loading.value = false
  }
}

// 获取粒子样式
const getParticleStyle = (index: number) => {
  const positions = [
    { top: '10%', left: '10%' },
    { top: '20%', left: '80%' },
    { top: '30%', left: '30%' },
    { top: '40%', left: '70%' },
    { top: '50%', left: '20%' },
    { top: '60%', left: '60%' },
    { top: '70%', left: '40%' },
    { top: '80%', left: '90%' },
    { top: '15%', left: '50%' },
    { top: '25%', left: '15%' },
    { top: '35%', left: '85%' },
    { top: '45%', left: '45%' },
    { top: '55%', left: '25%' },
    { top: '65%', left: '75%' },
    { top: '75%', left: '55%' },
    { top: '85%', left: '35%' },
    { top: '12%', left: '65%' },
    { top: '22%', left: '25%' },
    { top: '32%', left: '95%' },
    { top: '42%', left: '5%' }
  ]

  const delays = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
  const sizes = [2, 3, 2, 4, 2, 3, 2, 3, 2, 4, 2, 3, 2, 3, 2, 4, 2, 3, 2, 3]

  return {
    top: positions[index - 1]?.top || '50%',
    left: positions[index - 1]?.left || '50%',
    animationDelay: `${delays[index - 1] || 0}s`,
    width: `${sizes[index - 1] || 2}px`,
    height: `${sizes[index - 1] || 2}px`
  }
}

// 组件挂载时检查是否已登录
onMounted(async () => {
  await authStore.initAuth()
  if (authStore.isAuthenticated) {
    router.push('/dashboard')
  }
})
</script>

<style scoped>
/* LOGIN CONTAINER */
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: radial-gradient(circle at 20% -10%, rgba(153, 186, 255, 0.45), transparent 42%), linear-gradient(180deg, #f8faff 0%, #eef3fc 100%);
}

/* BACKGROUND EFFECTS */
.login-bg-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(var(--color-border-secondary) 1px, transparent 1px),
    linear-gradient(90deg, var(--color-border-secondary) 1px, transparent 1px);
  background-size: 50px 50px;
  opacity: 0.3;
  z-index: 1;
}

.login-bg-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(
    ellipse at 50% 0%,
    rgba(0, 122, 255, 0.06) 0%,
    rgba(90, 200, 250, 0.03) 30%,
    transparent 70%
  );
  z-index: 2;
}

.login-bg-scanline {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  z-index: 3;
  pointer-events: none;
}

.login-bg-scanline::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(
    90deg,
    transparent,
    var(--color-accent-primary),
    transparent
  );
  opacity: 0.15;
  animation: scanline 10s linear infinite;
}

@keyframes scanline {
  0% { top: 0; }
  100% { top: 100%; }
}

/* Particles */
.particles {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 4;
  pointer-events: none;
}

.particle {
  position: absolute;
  background: var(--color-accent-primary);
  border-radius: 50%;
  opacity: 0.3;
  animation: particle-float 20s linear infinite;
}

@keyframes particle-float {
  0%, 100% {
    transform: translateY(0) translateX(0);
    opacity: 0.3;
  }
  25% {
    transform: translateY(-20px) translateX(10px);
    opacity: 0.5;
  }
  50% {
    transform: translateY(-10px) translateX(-10px);
    opacity: 0.3;
  }
  75% {
    transform: translateY(-30px) translateX(5px);
    opacity: 0.6;
  }
}

/* Corner Decorations */
.corner {
  position: absolute;
  width: 100px;
  height: 100px;
  border: 2px solid var(--color-accent-primary);
  opacity: 0.2;
  z-index: 5;
  pointer-events: none;
}

.corner-tl {
  top: 40px;
  left: 40px;
  border-right: none;
  border-bottom: none;
}

.corner-tr {
  top: 40px;
  right: 40px;
  border-left: none;
  border-bottom: none;
}

.corner-bl {
  bottom: 40px;
  left: 40px;
  border-right: none;
  border-top: none;
}

.corner-br {
  bottom: 40px;
  right: 40px;
  border-left: none;
  border-top: none;
}

/* AUTH CARD */
.auth-card {
  position: relative;
  width: 420px;
  padding: var(--spacing-10);
  background: linear-gradient(180deg, rgba(255,255,255,0.94) 0%, rgba(248,251,255,0.92) 100%);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--border-radius-2xl);
  backdrop-filter: blur(20px);
  box-shadow:
    0 0 0 1px rgba(0, 122, 255, 0.08),
    0 8px 32px rgba(0, 0, 0, 0.08),
    0 0 0 1px var(--color-border-secondary);
  z-index: 10;
}

.auth-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    var(--color-accent-primary),
    transparent
  );
  opacity: 0.5;
}

/* HEADER */
.auth-header {
  text-align: center;
  margin-bottom: var(--spacing-8);
}

.logo-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--spacing-6);
  position: relative;
}

.logo-icon svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 0 10px var(--color-accent-glow));
  animation: logo-pulse 3s ease-in-out infinite;
}

@keyframes logo-pulse {
  0%, 100% {
    filter: drop-shadow(0 0 10px var(--color-accent-glow));
  }
  50% {
    filter: drop-shadow(0 0 20px var(--color-accent-glow));
  }
}

.auth-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-2) 0;
  letter-spacing: var(--letter-spacing-wide);
}

.auth-subtitle {
  font-size: var(--font-size-sm);
  font-family: var(--font-family-mono);
  color: var(--color-text-tertiary);
  margin: 0;
  letter-spacing: var(--letter-spacing-wider);
  text-transform: uppercase;
}

/* TABS */
.auth-tabs {
  position: relative;
  display: flex;
  background: var(--color-bg-tertiary);
  border-radius: var(--border-radius-md);
  padding: 4px;
  margin-bottom: var(--spacing-8);
}

.tab-btn {
  flex: 1;
  padding: var(--spacing-3) var(--spacing-4);
  background: transparent;
  border: none;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  position: relative;
  z-index: 1;
}

.tab-btn.active {
  color: var(--color-text-primary);
}

.tab-indicator {
  position: absolute;
  top: 4px;
  left: 4px;
  width: calc(50% - 4px);
  height: calc(100% - 8px);
  background: var(--color-accent-primary);
  border-radius: var(--border-radius-sm);
  transition: transform var(--duration-normal) var(--ease-spring);
}

/* FORM */
.auth-form {
  margin-bottom: var(--spacing-6);
}

.form-group {
  margin-bottom: var(--spacing-5);
}

.form-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-3);
  letter-spacing: var(--letter-spacing-wide);
  text-transform: uppercase;
}

.label-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-accent-primary);
}

.tech-input {
  --el-input-bg-color: var(--color-bg-tertiary);
  --el-input-text-color: var(--color-text-primary);
  --el-input-border-color: var(--color-border-primary);
  --el-input-hover-border-color: var(--color-accent-primary);
  --el-input-focus-border-color: var(--color-accent-primary);
  --el-input-placeholder-color: var(--color-text-tertiary);
}

.tech-input :deep(.el-input__wrapper) {
  background-color: var(--color-bg-tertiary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-3) var(--spacing-4);
  transition: all var(--duration-fast) var(--ease-out);
}

.tech-input :deep(.el-input__wrapper:hover) {
  border-color: var(--color-accent-primary);
}

.tech-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--color-accent-primary);
  box-shadow: 0 0 0 3px var(--color-accent-muted), 0 0 20px var(--color-accent-glow);
}

.tech-input :deep(.el-input__inner) {
  color: var(--color-text-primary);
  font-family: var(--font-family-mono);
  font-size: var(--font-size-sm);
}

.tech-input :deep(.el-input__prefix) {
  color: var(--color-text-tertiary);
}

/* FORM ACTIONS */
.form-actions {
  margin-top: var(--spacing-8);
}

.submit-btn {
  width: 100%;
  height: 48px;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--letter-spacing-wide);
  background: linear-gradient(
    135deg,
    var(--color-accent-primary) 0%,
    var(--color-info-primary) 100%
  );
  border: none;
  color: var(--color-bg-primary);
  position: relative;
  overflow: hidden;
}

.submit-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: left var(--duration-slow) var(--ease-out);
}

.submit-btn:hover::before {
  left: 100%;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px var(--color-accent-glow);
}

/* FORM FOOTER */
.form-footer {
  padding-top: var(--spacing-4);
}

.admin-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
  background: var(--color-bg-tertiary);
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-xs);
}

.hint-label {
  color: var(--color-text-tertiary);
}

.hint-value {
  color: var(--color-accent-primary);
  font-family: var(--font-family-mono);
  font-weight: var(--font-weight-medium);
}

/* AUTH FOOTER */
.auth-footer {
  padding-top: var(--spacing-6);
  border-top: 1px solid var(--color-border-secondary);
}

.footer-info {
  display: flex;
  justify-content: center;
  gap: var(--spacing-8);
}

.info-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-xs);
  font-family: var(--font-family-mono);
  color: var(--color-text-tertiary);
  letter-spacing: var(--letter-spacing-wide);
}

.info-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--color-accent-primary);
  animation: dot-pulse 2s ease-in-out infinite;
}

.info-dot.warning {
  background-color: var(--color-warning-primary);
}

@keyframes dot-pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.8);
  }
}

/* RESPONSIVE */
@media (max-width: 480px) {
  .auth-card {
    width: calc(100% - var(--spacing-8));
    padding: var(--spacing-8);
  }

  .corner {
    display: none;
  }
}
</style>

