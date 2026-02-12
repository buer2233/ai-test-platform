<template>
  <el-tag :type="statusType" :effect="effect">
    <el-icon v-if="statusIcon" class="status-icon">
      <component :is="statusIcon" />
    </el-icon>
    {{ statusText }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Clock,
  Loading,
  CircleCloseFilled,
  CircleCheck
} from '@element-plus/icons-vue'
import type { ExecutionStatus } from '../types/execution'

interface Props {
  status: ExecutionStatus | undefined
  effect?: 'dark' | 'light' | 'plain'
}

const props = withDefaults(defineProps<Props>(), {
  effect: 'light'
})

const statusType = computed(() => {
  const types: Record<ExecutionStatus, any> = {
    pending: 'info',
    running: 'warning',
    passed: 'success',
    failed: 'danger',
    error: 'danger',
    cancelled: 'info'
  }
  return props.status ? types[props.status] : 'info'
})

const statusText = computed(() => {
  const texts: Record<ExecutionStatus, string> = {
    pending: '待执行',
    running: '执行中',
    passed: '通过',
    failed: '失败',
    error: '错误',
    cancelled: '已取消'
  }
  return props.status ? texts[props.status] : '未知'
})

const statusIcon = computed(() => {
  const icons: Record<ExecutionStatus, any> = {
    pending: Clock,
    running: Loading,
    passed: CircleCheck,
    failed: CircleCloseFilled,
    error: CircleCloseFilled,
    cancelled: CircleCloseFilled
  }
  return props.status ? icons[props.status] : null
})
</script>

<style scoped>
.status-icon {
  margin-right: 4px;
}

.status-icon.is-running {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
