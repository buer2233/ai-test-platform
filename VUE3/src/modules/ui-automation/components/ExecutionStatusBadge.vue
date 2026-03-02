<template>
  <el-tag :type="statusType" :effect="effect">
    <el-icon v-if="statusIcon" class="status-icon">
      <component :is="statusIcon" />
    </el-icon>
    {{ statusText }}
  </el-tag>
</template>

<script setup lang="ts">
/**
 * 执行状态徽章组件
 *
 * 根据执行状态显示对应的颜色、图标和文本标签。
 * 用于执行列表、监控页面等场景中直观展示执行结果。
 */

import { computed } from 'vue'
import {
  CircleCheck,
  CircleCloseFilled,
  Clock,
  Loading
} from '@element-plus/icons-vue'

import type { ExecutionStatus } from '../types/execution'

interface Props {
  /** 执行状态值 */
  status: ExecutionStatus | undefined
  /** El-Tag 样式效果 */
  effect?: 'dark' | 'light' | 'plain'
}

const props = withDefaults(defineProps<Props>(), {
  effect: 'light'
})

/** 状态 -> El-Tag 类型的映射 */
const STATUS_TYPE_MAP: Record<ExecutionStatus, string> = {
  pending: 'info',
  running: 'warning',
  passed: 'success',
  failed: 'danger',
  error: 'danger',
  cancelled: 'info'
}

/** 状态 -> 中文文本的映射 */
const STATUS_TEXT_MAP: Record<ExecutionStatus, string> = {
  pending: '待执行',
  running: '执行中',
  passed: '通过',
  failed: '失败',
  error: '错误',
  cancelled: '已取消'
}

/** 状态 -> 图标组件的映射 */
const STATUS_ICON_MAP: Record<ExecutionStatus, any> = {
  pending: Clock,
  running: Loading,
  passed: CircleCheck,
  failed: CircleCloseFilled,
  error: CircleCloseFilled,
  cancelled: CircleCloseFilled
}

/** 当前状态对应的 El-Tag 类型 */
const statusType = computed(() => {
  return props.status ? STATUS_TYPE_MAP[props.status] : 'info'
})

/** 当前状态对应的中文文本 */
const statusText = computed(() => {
  return props.status ? STATUS_TEXT_MAP[props.status] : '未知'
})

/** 当前状态对应的图标组件 */
const statusIcon = computed(() => {
  return props.status ? STATUS_ICON_MAP[props.status] : null
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
