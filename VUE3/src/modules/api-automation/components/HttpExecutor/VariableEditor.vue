<template>
  <div class="variable-editor">
    <div class="editor-header">
      <div class="header-left">
        <h4>全局变量配置</h4>
        <el-tooltip content="变量可以在请求的任何部分使用，格式：${变量名}">
          <el-icon style="color: #909399; margin-left: 5px;"><QuestionFilled /></el-icon>
        </el-tooltip>
      </div>
      <div class="header-right">
        <el-button
          size="small"
          type="primary"
          @click="addVariable"
          :icon="Plus"
        >
          添加变量
        </el-button>
        <el-button
          size="small"
          @click="importEnvironmentVariables"
          v-if="environments.length > 0"
        >
          导入环境变量
        </el-button>
        <el-button
          size="small"
          @click="exportVariables"
          :disabled="variables.length === 0"
        >
          导出变量
        </el-button>
      </div>
    </div>

    <div class="variable-list">
      <div
        v-for="(variable, index) in variables"
        :key="index"
        class="variable-item"
        :class="{ 'item-disabled': !variable.enabled }"
      >
        <div class="variable-main">
          <el-checkbox
            v-model="variable.enabled"
            @change="onEnabledChange(index)"
          />
          <el-input
            v-model="variable.name"
            placeholder="变量名"
            size="small"
            class="variable-name"
            @blur="validateVariableName(index)"
          />
          <el-select
            v-model="variable.type"
            size="small"
            class="variable-type"
            @change="onTypeChange(index)"
          >
            <el-option label="字符串" value="string" />
            <el-option label="数字" value="number" />
            <el-option label="布尔值" value="boolean" />
            <el-option label="JSON" value="json" />
            <el-option label="环境变量" value="environment" />
          </el-select>
          <el-input
            v-if="variable.type === 'boolean'"
            v-model="variable.value"
            size="small"
            class="variable-value"
          >
            <template #suffix>
              <el-select
                v-model="variable.value"
                size="small"
                style="width: 80px; margin-right: -10px;"
              >
                <el-option label="true" value="true" />
                <el-option label="false" value="false" />
              </el-select>
            </template>
          </el-input>
          <el-input-number
            v-else-if="variable.type === 'number'"
            v-model="variableValueNumber[index]"
            size="small"
            class="variable-value"
            @change="onNumberChange(index)"
          />
          <el-select
            v-else-if="variable.type === 'environment'"
            v-model="variable.value"
            size="small"
            class="variable-value"
            filterable
            allow-create
          >
            <el-option
              v-for="env in availableEnvVars"
              :key="env.name"
              :label="`${env.name} (${env.source})`"
              :value="env.name"
            />
          </el-select>
          <el-input
            v-else
            v-model="variable.value"
            :placeholder="getValuePlaceholder(variable.type)"
            size="small"
            class="variable-value"
            type="textarea"
            :rows="variable.type === 'json' ? 3 : 1"
          />
        </div>
        <div class="variable-actions">
          <el-tooltip content="测试变量" placement="top">
            <el-button
              size="small"
              type="text"
              @click="testVariable(index)"
            >
              <el-icon><CaretRight /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="复制变量" placement="top">
            <el-button
              size="small"
              type="text"
              @click="copyVariable(index)"
            >
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="删除变量" placement="top">
            <el-button
              size="small"
              type="text"
              style="color: #f56c6c;"
              @click="removeVariable(index)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>

      <div v-if="variables.length === 0" class="empty-state">
        <el-empty description="暂无变量配置" :image-size="80">
          <el-button type="primary" @click="addVariable">添加第一个变量</el-button>
        </el-empty>
      </div>
    </div>

    <!-- 变量使用情况 -->
    <div class="variable-usage" v-if="usageInfo.length > 0">
      <h4>变量使用情况</h4>
      <el-table :data="usageInfo" size="small">
        <el-table-column prop="name" label="变量名" width="150" />
        <el-table-column prop="usage" label="使用位置" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag
              :type="row.defined ? 'success' : 'danger'"
              size="small"
            >
              {{ row.defined ? '已定义' : '未定义' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 导入环境变量对话框 -->
    <el-dialog
      title="导入环境变量"
      v-model="importDialogVisible"
      width="600px"
    >
      <div class="import-env-vars">
        <el-form :model="importForm" label-width="100px">
          <el-form-item label="环境选择">
            <el-select v-model="importForm.environment" style="width: 100%">
              <el-option
                v-for="env in environments"
                :key="env.id"
                :label="env.name"
                :value="env.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="变量类型">
            <el-checkbox-group v-model="importForm.types">
              <el-checkbox label="global">全局变量</el-checkbox>
              <el-checkbox label="env">环境变量</el-checkbox>
              <el-checkbox label="system">系统变量</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </el-form>

        <div class="env-var-preview" v-if="previewVars.length > 0">
          <h4>预览（共 {{ previewVars.length }} 个变量）</h4>
          <el-table :data="previewVars.slice(0, 10)" size="small" max-height="300">
            <el-table-column prop="name" label="变量名" />
            <el-table-column prop="value" label="值" show-overflow-tooltip />
            <el-table-column prop="source" label="来源" width="100" />
          </el-table>
          <div v-if="previewVars.length > 10" class="preview-more">
            还有 {{ previewVars.length - 10 }} 个变量...
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="confirmImport"
          :disabled="!importForm.environment || previewVars.length === 0"
        >
          确认导入
        </el-button>
      </template>
    </el-dialog>

    <!-- 变量测试对话框 -->
    <el-dialog
      title="测试变量"
      v-model="testDialogVisible"
      width="500px"
    >
      <div class="variable-test">
        <el-form :model="testForm" label-width="80px">
          <el-form-item label="变量名">
            <el-input v-model="testForm.name" readonly />
          </el-form-item>
          <el-form-item label="变量值">
            <el-input v-model="testForm.value" readonly />
          </el-form-item>
          <el-form-item label="测试表达式">
            <el-input
              v-model="testForm.expression"
              placeholder="输入包含变量的表达式，如：${variable}"
            />
          </el-form-item>
          <el-form-item label="替换结果">
            <el-input
              v-model="testResult"
              readonly
              type="textarea"
              :rows="3"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="executeTest">执行测试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Delete,
  CopyDocument,
  CaretRight,
  QuestionFilled
} from '@element-plus/icons-vue'
import { useEnvironmentStore } from '../../stores/environment'

interface Variable {
  name: string
  value: string
  type: 'string' | 'number' | 'boolean' | 'json' | 'environment'
  enabled: boolean
  description?: string
}

interface Props {
  modelValue: Variable[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: Variable[]]
}>()

// Store
const environmentStore = useEnvironmentStore()

// 响应式数据
const variables = ref<Variable[]>([])
const variableValueNumber = ref<number[]>([])
const importDialogVisible = ref(false)
const testDialogVisible = ref(false)
const testResult = ref('')

// 导入表单
const importForm = reactive({
  environment: null,
  types: ['global', 'env']
})

// 测试表单
const testForm = reactive({
  name: '',
  value: '',
  expression: ''
})

// 计算属性
const environments = computed(() => environmentStore.environments)

const availableEnvVars = computed(() => {
  const vars = []

  // 系统环境变量
  vars.push(
    { name: 'BASE_URL', source: '系统' },
    { name: 'API_VERSION', source: '系统' },
    { name: 'TIMESTAMP', source: '系统' },
    { name: 'UUID', source: '系统' }
  )

  // 从已配置环境获取变量
  environments.value.forEach(env => {
    if (env.global_variables) {
      Object.keys(env.global_variables).forEach(key => {
        vars.push({
          name: key,
          source: env.name
        })
      })
    }
  })

  return vars
})

const previewVars = computed(() => {
  if (!importForm.environment) return []

  const env = environments.value.find(e => e.id === importForm.environment)
  if (!env) return []

  const vars = []

  if (importForm.types.includes('global') && env.global_variables) {
    Object.entries(env.global_variables).forEach(([key, value]) => {
      vars.push({
        name: key,
        value: String(value),
        source: '全局变量'
      })
    })
  }

  return vars
})

const usageInfo = computed(() => {
  // 这里应该从父组件获取使用情况
  // 暂时返回空数组
  return []
})

// 方法
const addVariable = () => {
  variables.value.push({
    name: '',
    value: '',
    type: 'string',
    enabled: true,
    description: ''
  })
  emitUpdate()
}

const removeVariable = (index: number) => {
  variables.value.splice(index, 1)
  emitUpdate()
}

const onEnabledChange = (index: number) => {
  emitUpdate()
}

const onTypeChange = (index: number) => {
  const variable = variables.value[index]
  if (variable.type === 'number') {
    variableValueNumber.value[index] = Number(variable.value) || 0
  } else if (variable.type === 'boolean') {
    variable.value = 'false'
  }
  emitUpdate()
}

const onNumberChange = (index: number) => {
  variables.value[index].value = String(variableValueNumber.value[index])
  emitUpdate()
}

const getValuePlaceholder = (type: string) => {
  const placeholders = {
    string: '输入字符串值',
    number: '输入数字值',
    boolean: '选择布尔值',
    json: '输入JSON对象',
    environment: '选择环境变量'
  }
  return placeholders[type] || '输入值'
}

const validateVariableName = (index: number) => {
  const variable = variables.value[index]
  if (!variable.name) return

  // 检查变量名格式
  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(variable.name)) {
    ElMessage.warning(`变量名 "${variable.name}" 格式不正确，应以字母或下划线开头`)
    return
  }

  // 检查重复
  const duplicates = variables.value.filter((v, i) =>
    v.name === variable.name && i !== index
  )
  if (duplicates.length > 0) {
    ElMessage.warning(`变量名 "${variable.name}" 已存在`)
  }
}

const copyVariable = (index: number) => {
  const variable = variables.value[index]
  const newVariable = {
    ...variable,
    name: `${variable.name}_copy`,
    enabled: true
  }
  variables.value.splice(index + 1, 0, newVariable)
  emitUpdate()
}

const testVariable = (index: number) => {
  const variable = variables.value[index]
  testForm.name = variable.name
  testForm.value = variable.value
  testForm.expression = `\${${variable.name}}`
  testDialogVisible.value = true
}

const executeTest = () => {
  // 这里应该执行变量替换
  testResult.value = testForm.expression.replace(
    new RegExp(`\\$\\{${testForm.name}\\}`, 'g'),
    testForm.value
  )
}

const importEnvironmentVariables = () => {
  importDialogVisible.value = true
}

const confirmImport = () => {
  previewVars.value.forEach(v => {
    // 检查是否已存在
    const existing = variables.value.find(vari => vari.name === v.name)
    if (!existing) {
      variables.value.push({
        name: v.name,
        value: v.value,
        type: typeof v.value === 'number' ? 'number' : 'string',
        enabled: true,
        description: `从${v.source}导入`
      })
    }
  })

  importDialogVisible.value = false
  emitUpdate()
  ElMessage.success(`成功导入 ${previewVars.value.length} 个变量`)
}

const exportVariables = () => {
  const data = variables.value.filter(v => v.enabled).map(v => ({
    name: v.name,
    value: v.value,
    type: v.type,
    description: v.description
  }))

  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json'
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `variables_${Date.now()}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  ElMessage.success('变量配置已导出')
}

const emitUpdate = () => {
  emit('update:modelValue', variables.value)
}

// 监听器
watch(() => props.modelValue, (newValue) => {
  variables.value = newValue.map(v => ({
    ...v,
    enabled: v.enabled !== false
  }))
  variableValueNumber.value = variables.value.map(v =>
    v.type === 'number' ? Number(v.value) || 0 : 0
  )
}, { immediate: true, deep: true })

// 生命周期
const loadEnvironments = () => {
  environmentStore.fetchEnvironments()
}

loadEnvironments()
</script>

<style scoped>
.variable-editor {
  padding: 10px;
}

.editor-header {
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
}

.header-left h4 {
  margin: 0;
  font-size: 16px;
}

.header-right {
  display: flex;
  gap: 10px;
}

.variable-list {
  max-height: 500px;
  overflow-y: auto;
}

.variable-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 10px;
}

.variable-item:hover {
  border-color: #c6e2ff;
  background: #f5f7fa;
}

.item-disabled {
  opacity: 0.6;
}

.variable-main {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.variable-name {
  width: 180px;
}

.variable-type {
  width: 120px;
}

.variable-value {
  flex: 1;
}

.variable-actions {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-left: 10px;
}

.empty-state {
  padding: 40px;
  text-align: center;
}

.variable-usage {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.variable-usage h4 {
  margin-bottom: 15px;
}

.import-env-vars {
  padding: 10px 0;
}

.env-var-preview {
  margin-top: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.env-var-preview h4 {
  margin: 0 0 10px 0;
}

.preview-more {
  text-align: center;
  color: #909399;
  margin-top: 10px;
}

.variable-test {
  padding: 10px 0;
}
</style>