<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="550px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="delete-confirm-content">
      <!-- 警告图标 -->
      <div class="warning-icon">
        <el-icon :size="48" color="#F56C6C">
          <WarningFilled />
        </el-icon>
      </div>

      <!-- 确认信息 -->
      <div class="confirm-message">
        <p class="main-message">{{ mainMessage }}</p>
        <p v-if="targetInfo" class="target-info">
          <strong>{{ targetInfo.display_type }}:</strong> {{ targetInfo.name }}
        </p>
      </div>

      <!-- 级联删除预览 -->
      <div v-if="preview && hasCascadeItems" class="cascade-preview">
        <div class="preview-header">
          <el-icon class="header-icon"><InfoFilled /></el-icon>
          <span>以下关联数据也将被删除:</span>
        </div>

        <el-scrollbar max-height="200px">
          <div class="cascade-list">
            <div
              v-for="(item, index) in preview.cascade_details"
              :key="index"
              class="cascade-item"
            >
              <div class="item-header">
                <el-tag :type="getTagType(item.type)" size="small">
                  {{ item.display_type }}
                </el-tag>
                <span class="item-count">{{ item.count }} 个</span>
              </div>
              <div v-if="item.names && item.names.length > 0" class="item-names">
                <el-tooltip
                  v-for="(name, idx) in item.names.slice(0, 5)"
                  :key="idx"
                  :content="name"
                  placement="top"
                >
                  <span class="name-tag">{{ name }}</span>
                </el-tooltip>
                <span v-if="item.names.length > 5" class="more-hint">
                  等{{ item.count }}个
                </span>
              </div>
            </div>
          </div>
        </el-scrollbar>
      </div>

      <!-- 空提示 -->
      <div v-else-if="preview && !hasCascadeItems" class="no-cascade">
        <el-icon class="check-icon"><SuccessFilled /></el-icon>
        <span>无关联数据，仅删除当前项</span>
      </div>

      <!-- 二次确认 -->
      <div v-if="requireConfirm" class="confirm-check">
        <el-checkbox v-model="confirmed">
          我已了解删除操作的影响，确认要继续
        </el-checkbox>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="danger"
          :loading="loading"
          :disabled="requireConfirm && !confirmed"
          @click="handleConfirm"
        >
          {{ confirmButtonText }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { WarningFilled, InfoFilled, SuccessFilled } from '@element-plus/icons-vue'
import type { CascadePreviewResponse } from '../api/recycleBin'

interface Props {
  modelValue: boolean
  title?: string
  targetInfo?: {
    id: number
    name: string
    type: string
    display_type: string
  }
  preview?: CascadePreviewResponse | null
  confirmButtonText?: string
  loading?: boolean
  requireConfirm?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm'): void
}

const props = withDefaults(defineProps<Props>(), {
  title: '确认删除',
  confirmButtonText: '确认删除',
  loading: false,
  requireConfirm: true
})

const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const confirmed = ref(false)

// 监听对话框打开状态，重置确认
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    confirmed.value = false
  }
})

const mainMessage = computed(() => {
  if (hasCascadeItems.value) {
    return '此操作将删除选中数据及其所有关联数据，删除后可从回收站恢复。'
  }
  return '此操作将删除选中数据，删除后可从回收站恢复。'
})

const hasCascadeItems = computed(() => {
  return props.preview &&
         Object.keys(props.preview.cascade_count).length > 0 &&
         Object.values(props.preview.cascade_count).some(v => v > 0)
})

const getTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    'apicollection': 'primary',
    'apitestcase': 'success',
    'apitestenvironment': 'warning',
    'apidatadriver': 'info'
  }
  return typeMap[type] || 'default'
}

const handleClose = () => {
  visible.value = false
}

const handleConfirm = () => {
  emit('confirm')
}
</script>

<style scoped lang="scss">
.delete-confirm-content {
  padding: 10px 0;

  .warning-icon {
    text-align: center;
    margin-bottom: 20px;
  }

  .confirm-message {
    text-align: center;
    margin-bottom: 20px;

    .main-message {
      font-size: 16px;
      color: #303133;
      margin-bottom: 8px;
    }

    .target-info {
      font-size: 14px;
      color: #606266;
    }
  }

  .cascade-preview {
    margin-top: 20px;
    border: 1px solid #E4E7ED;
    border-radius: 4px;
    overflow: hidden;

    .preview-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 16px;
      background: #F5F7FA;
      border-bottom: 1px solid #E4E7ED;
      font-size: 14px;
      color: #606266;

      .header-icon {
        color: #409EFF;
      }
    }

    .cascade-list {
      padding: 12px 16px;
    }

    .cascade-item {
      padding: 10px 0;
      border-bottom: 1px solid #F5F7FA;

      &:last-child {
        border-bottom: none;
      }

      .item-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;

        .item-count {
          font-size: 12px;
          color: #909399;
        }
      }

      .item-names {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        padding-left: 4px;

        .name-tag {
          display: inline-block;
          max-width: 120px;
          padding: 2px 8px;
          font-size: 12px;
          color: #606266;
          background: #F5F7FA;
          border-radius: 3px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .more-hint {
          font-size: 12px;
          color: #909399;
          padding: 2px 0;
        }
      }
    }
  }

  .no-cascade {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 20px;
    background: #F0F9FF;
    border-radius: 4px;
    color: #67C23A;
    font-size: 14px;

    .check-icon {
      font-size: 20px;
    }
  }

  .confirm-check {
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid #E4E7ED;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
