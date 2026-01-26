<template>
  <div class="test-results">
    <div class="results-header">
      <div class="header-left">
        <h4>断言测试结果</h4>
        <el-tag
          :type="overallStatus === 'passed' ? 'success' : 'danger'"
          size="small"
        >
          {{ overallStatus === 'passed' ? '全部通过' : '存在失败' }}
        </el-tag>
      </div>
      <div class="header-right">
        <span class="stats">
          通过: <strong class="passed">{{ passedCount }}</strong> /
          失败: <strong class="failed">{{ failedCount }}</strong> /
          总计: <strong>{{ totalCount }}</strong>
        </span>
      </div>
    </div>

    <div class="results-content">
      <div v-if="tests.length === 0" class="empty-state">
        <el-empty description="暂无断言测试" :image-size="80">
          <template #description>
            <p>请在请求配置中添加断言测试</p>
          </template>
        </el-empty>
      </div>

      <div v-else class="test-list">
        <div
          v-for="(test, index) in tests"
          :key="index"
          class="test-item"
          :class="{
            'test-passed': test.status === 'PASSED',
            'test-failed': test.status === 'FAILED',
            'test-skipped': test.status === 'SKIPPED'
          }"
        >
          <div class="test-header">
            <div class="test-info">
              <el-icon class="test-icon">
                <CircleCheckFilled v-if="test.status === 'PASSED'" />
                <CircleCloseFilled v-else-if="test.status === 'FAILED'" />
                <RemoveFilled v-else />
              </el-icon>
              <span class="test-name">{{ test.name || `断言 ${index + 1}` }}</span>
              <el-tag
                :type="getStatusType(test.status)"
                size="small"
              >
                {{ getStatusText(test.status) }}
              </el-tag>
            </div>
            <div class="test-actions">
              <el-button
                size="small"
                type="text"
                @click="showTestDetail(test)"
              >
                详情
              </el-button>
            </div>
          </div>

          <div class="test-content">
            <div class="test-config">
              <div class="config-item">
                <span class="label">断言类型:</span>
                <span class="value">{{ test.assert_type }}</span>
              </div>
              <div class="config-item">
                <span class="label">目标:</span>
                <span class="value">{{ test.target }}</span>
              </div>
              <div class="config-item">
                <span class="label">操作符:</span>
                <span class="value">{{ test.operator }}</span>
              </div>
              <div class="config-item">
                <span class="label">期望值:</span>
                <span class="value">{{ formatExpectedValue(test.expected_value) }}</span>
              </div>
            </div>

            <div v-if="test.status === 'FAILED'" class="test-error">
              <div class="error-header">
                <el-icon><WarningFilled /></el-icon>
                <span>失败原因</span>
              </div>
              <div class="error-message">
                {{ test.error_message || '断言失败' }}
              </div>
            </div>

            <div v-if="test.status === 'PASSED'" class="test-success">
              <div class="success-header">
                <el-icon><SuccessFilled /></el-icon>
                <span>断言通过</span>
              </div>
              <div class="success-message">
                实际值: {{ formatActualValue(test.actual_value) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 测试详情对话框 -->
    <el-dialog
      title="断言测试详情"
      v-model="detailDialogVisible"
      width="60%"
      top="5vh"
    >
      <div v-if="currentTest" class="test-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="测试名称">
            {{ currentTest.name || `断言 ${tests.indexOf(currentTest) + 1}` }}
          </el-descriptions-item>
          <el-descriptions-item label="测试状态">
            <el-tag :type="getStatusType(currentTest.status)">
              {{ getStatusText(currentTest.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="断言类型" span="2">
            {{ currentTest.assert_type }}
          </el-descriptions-item>
          <el-descriptions-item label="目标路径" span="2">
            <code>{{ currentTest.target }}</code>
          </el-descriptions-item>
          <el-descriptions-item label="操作符">
            {{ currentTest.operator }}
          </el-descriptions-item>
          <el-descriptions-item label="期望值">
            <code>{{ formatExpectedValue(currentTest.expected_value) }}</code>
          </el-descriptions-item>
          <el-descriptions-item label="实际值" v-if="currentTest.actual_value !== undefined">
            <code>{{ formatActualValue(currentTest.actual_value) }}</code>
          </el-descriptions-item>
          <el-descriptions-item label="执行时间" v-if="currentTest.execution_time">
            {{ currentTest.execution_time }}ms
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="currentTest.status === 'FAILED'" class="detail-error">
          <h4>错误信息</h4>
          <el-alert
            :title="currentTest.error_message || '断言失败'"
            type="error"
            :closable="false"
          />
        </div>

        <div v-if="currentTest.debug_info" class="debug-info">
          <h4>调试信息</h4>
          <pre class="debug-content">{{ JSON.stringify(currentTest.debug_info, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  CircleCheckFilled,
  CircleCloseFilled,
  RemoveFilled,
  WarningFilled,
  SuccessFilled
} from '@element-plus/icons-vue'

interface TestAssertion {
  name?: string
  assert_type: string
  target: string
  operator: string
  expected_value: any
  actual_value?: any
  status: 'PASSED' | 'FAILED' | 'SKIPPED'
  error_message?: string
  execution_time?: number
  debug_info?: any
}

interface ResponseData {
  status: number
  headers: Record<string, string>
  body: any
  response_time: number
  body_size: number
}

interface Props {
  tests: TestAssertion[]
  response: ResponseData
}

const props = defineProps<Props>()

// 响应式数据
const detailDialogVisible = ref(false)
const currentTest = ref<TestAssertion | null>(null)

// 计算属性
const passedCount = computed(() =>
  props.tests.filter(t => t.status === 'PASSED').length
)

const failedCount = computed(() =>
  props.tests.filter(t => t.status === 'FAILED').length
)

const totalCount = computed(() => props.tests.length)

const overallStatus = computed(() =>
  failedCount.value === 0 ? 'passed' : 'failed'
)

// 方法
const getStatusType = (status: string) => {
  const typeMap = {
    'PASSED': 'success',
    'FAILED': 'danger',
    'SKIPPED': 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap = {
    'PASSED': '通过',
    'FAILED': '失败',
    'SKIPPED': '跳过'
  }
  return textMap[status] || status
}

const formatExpectedValue = (value: any) => {
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

const formatActualValue = (value: any) => {
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

const showTestDetail = (test: TestAssertion) => {
  currentTest.value = test
  detailDialogVisible.value = true
}
</script>

<style scoped>
.test-results {
  padding: 10px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-left h4 {
  margin: 0;
  font-size: 16px;
}

.header-right .stats {
  font-size: 14px;
  color: #606266;
}

.stats .passed {
  color: #67c23a;
}

.stats .failed {
  color: #f56c6c;
}

.results-content {
  max-height: 500px;
  overflow-y: auto;
}

.empty-state {
  padding: 40px;
  text-align: center;
}

.test-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.test-item {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
  transition: all 0.2s;
}

.test-item:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.test-passed {
  border-left: 4px solid #67c23a;
}

.test-failed {
  border-left: 4px solid #f56c6c;
}

.test-skipped {
  border-left: 4px solid #909399;
}

.test-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
}

.test-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.test-icon {
  font-size: 16px;
}

.test-passed .test-icon {
  color: #67c23a;
}

.test-failed .test-icon {
  color: #f56c6c;
}

.test-skipped .test-icon {
  color: #909399;
}

.test-name {
  font-weight: 500;
  color: #303133;
}

.test-content {
  padding: 16px;
}

.test-config {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 15px;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-item .label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
}

.config-item .value {
  color: #303133;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  word-break: break-all;
}

.test-error,
.test-success {
  padding: 12px;
  border-radius: 4px;
  margin-top: 10px;
}

.test-error {
  background: #fef0f0;
  border: 1px solid #fde2e2;
}

.test-success {
  background: #f0f9ff;
  border: 1px solid #e1f3d8;
}

.error-header,
.success-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  margin-bottom: 8px;
}

.error-header {
  color: #f56c6c;
}

.success-header {
  color: #67c23a;
}

.error-message,
.success-message {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.test-detail {
  padding: 10px 0;
}

.detail-error {
  margin-top: 20px;
}

.detail-error h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.debug-info {
  margin-top: 20px;
}

.debug-info h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.debug-content {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
  margin: 0;
}
</style>