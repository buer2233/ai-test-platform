<template>
  <div class="natural-language-editor">
    <el-input
      v-model="internalValue"
      type="textarea"
      :placeholder="placeholder"
      :rows="rows"
      :maxlength="maxLength"
      show-word-limit
      @input="handleInput"
    />
    <div v-if="showTips" class="editor-tips">
      <div class="tips-title">
        <el-icon><InfoFilled /></el-icon>
        <span>编写提示</span>
      </div>
      <ul class="tips-list">
        <li>使用清晰的步骤序号（1. 2. 3. ...）</li>
        <li>描述要执行的操作，如"点击登录按钮"</li>
        <li>描述要验证的内容，如"验证显示用户名"</li>
        <li>可以使用自然语言，AI会自动解析并执行</li>
      </ul>
    </div>
    <div v-if="showExamples" class="editor-examples">
      <div class="examples-title">示例</div>
      <div class="example-item" @click="useExample(loginExample)">
        <span class="example-label">登录测试</span>
        <el-icon><ArrowRight /></el-icon>
      </div>
      <div class="example-item" @click="useExample(searchExample)">
        <span class="example-label">搜索测试</span>
        <el-icon><ArrowRight /></el-icon>
      </div>
      <div class="example-item" @click="useExample(formExample)">
        <span class="example-label">表单提交测试</span>
        <el-icon><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { InfoFilled, ArrowRight } from '@element-plus/icons-vue'

interface Props {
  modelValue: string
  placeholder?: string
  rows?: number
  maxLength?: number
  showTips?: boolean
  showExamples?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请用自然语言描述测试场景...',
  rows: 8,
  maxLength: 5000,
  showTips: true,
  showExamples: true
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const internalValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const handleInput = (value: string) => {
  emit('update:modelValue', value)
}

// 示例任务
const loginExample = `1. 打开登录页面
2. 在用户名输入框输入 "testuser"
3. 在密码输入框输入 "password123"
4. 点击登录按钮
5. 等待页面跳转
6. 验证页面显示欢迎信息`

const searchExample = `1. 打开百度首页 https://www.baidu.com
2. 在搜索框中输入 "browser_use AI测试"
3. 点击搜索按钮
4. 等待搜索结果加载完成
5. 验证搜索结果包含相关内容
6. 验证页面标题包含搜索关键词`

const formExample = `1. 打开注册页面
2. 输入用户名 "newuser"
3. 输入邮箱 "test@example.com"
4. 输入密码 "Pass123!"
5. 确认密码 "Pass123!"
6. 勾选用户协议复选框
7. 点击注册按钮
8. 验证显示注册成功提示
9. 验证跳转到首页`

const useExample = (example: string) => {
  emit('update:modelValue', example)
}
</script>

<style scoped>
.natural-language-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.editor-tips {
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  border-left: 3px solid var(--el-color-primary);
}

.tips-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.tips-list {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.tips-list li {
  margin-bottom: 4px;
}

.editor-examples {
  padding: 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}

.examples-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.example-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 8px;
}

.example-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.example-label {
  font-size: 13px;
  color: var(--el-text-color-primary);
}
</style>
