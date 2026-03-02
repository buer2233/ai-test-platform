/**
 * Element Plus 兼容层
 *
 * 本模块为项目提供了一套轻量化的 Element Plus 组件替代实现，
 * 目的是在不引入完整 Element Plus 库的情况下，提供必要的 UI 组件功能。
 *
 * 主要包含：
 * 1. 消息/通知/对话框 API（ElMessage、ElNotification、ElMessageBox）
 * 2. 表单相关组件（ElForm、ElFormItem、ElInput、ElSelect 等）
 * 3. 布局组件（ElRow、ElCol、ElCard、ElDialog 等）
 * 4. 导航组件（ElMenu、ElMenuItem、ElDropdown 等）
 * 5. 简单占位组件（通过 simple() 工厂函数批量生成）
 * 6. Vue 插件安装器（全局注册所有组件、指令和全局属性）
 */
import {
  computed,
  defineComponent,
  h,
  inject,
  nextTick,
  onMounted,
  onUnmounted,
  provide,
  ref,
  watch,
  type PropType
} from 'vue'
import type { App } from 'vue'
import { useRouter } from 'vue-router'

import './styles.css'

/* ========== 类型定义 ========== */

/** 表单规则验证器函数签名 */
type RuleValidator = (
  rule: Record<string, any>,
  value: unknown,
  callback: (error?: Error) => void
) => void | Promise<void>

/** 表单规则集合，键为字段名，值为该字段的验证规则数组 */
export type FormRules = Record<string, Array<Record<string, any> & { validator?: RuleValidator }>>

/** 表单实例方法接口，与 Element Plus ElForm 的 ref 方法保持一致 */
export interface FormInstance {
  validate: (callback?: (valid: boolean, fields?: Record<string, string>) => void) => Promise<boolean>
  validateField: (prop: string | string[], callback?: (errorMessage?: string) => void) => Promise<boolean>
  resetFields: (props?: string | string[]) => void
  clearValidate: (props?: string | string[]) => void
}

/* ========== 内部工具函数 ========== */

/** 将 PascalCase 转换为 kebab-case（如 ElButton -> el-button） */
function toKebab(input: string): string {
  return input.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase()
}

/** 判断值是否为空（空字符串、null、undefined 或空数组） */
function isEmpty(value: unknown): boolean {
  if (Array.isArray(value)) {
    return value.length === 0
  }
  return value === '' || value === null || value === undefined
}

/**
 * 执行单条表单验证规则
 *
 * 按优先级依次检查：必填 -> 长度范围 -> 正则 -> 邮箱格式 -> 自定义验证器
 * 验证失败时抛出 Error，由调用方捕获
 */
async function runRule(rule: Record<string, any>, value: unknown) {
  if (rule.required && isEmpty(value)) {
    throw new Error(rule.message || '请填写必填项')
  }

  if (value !== null && value !== undefined && value !== '') {
    const text = String(value)
    if (typeof rule.min === 'number' && text.length < rule.min) {
      throw new Error(rule.message || `长度不能小于${rule.min}`)
    }
    if (typeof rule.max === 'number' && text.length > rule.max) {
      throw new Error(rule.message || `长度不能大于${rule.max}`)
    }
    if (rule.pattern instanceof RegExp && !rule.pattern.test(text)) {
      throw new Error(rule.message || '格式不正确')
    }
    if (rule.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(text)) {
      throw new Error(rule.message || '邮箱格式不正确')
    }
  }

  if (typeof rule.validator === 'function') {
    await new Promise<void>((resolve, reject) => {
      const callback = (error?: Error) => (error ? reject(error) : resolve())
      try {
        const result = rule.validator(rule, value, callback)
        if (result && typeof (result as Promise<void>).then === 'function') {
          ;(result as Promise<void>).then(() => resolve()).catch(reject)
        }
      } catch (error) {
        reject(error)
      }
    })
  }
}

/* ========== Toast 消息提示系统 ========== */

/** Toast 容器的 DOM ID */
const ToastContainerId = '__el_compat_toasts__'

/** 获取或创建 Toast 容器 DOM 节点（固定在页面右上角） */
function toastContainer(): HTMLElement {
  let node = document.getElementById(ToastContainerId)
  if (!node) {
    node = document.createElement('div')
    node.id = ToastContainerId
    node.className = 'el-toast-container'
    document.body.appendChild(node)
  }
  return node
}

/** 创建并显示一条 Toast 消息，到达 duration 后自动关闭 */
function pushToast(type: string, message: string, duration = 2500) {
  if (typeof window === 'undefined') {
    return
  }
  const container = toastContainer()
  const node = document.createElement('div')
  node.className = `el-toast el-toast--${type}`
  node.textContent = message
  container.appendChild(node)

  requestAnimationFrame(() => {
    node.classList.add('is-visible')
  })

  const close = () => {
    node.classList.remove('is-visible')
    window.setTimeout(() => {
      if (container.contains(node)) {
        container.removeChild(node)
      }
    }, 180)
  }

  const timer = window.setTimeout(close, duration)
  return {
    close: () => {
      window.clearTimeout(timer)
      close()
    }
  }
}

/** 消息参数类型：支持纯字符串或包含 type/duration 的对象 */
type MessageParams = string | { message: string; type?: string; duration?: number }

/** 消息处理器，提供 close 方法用于手动关闭 */
interface MessageHandler {
  close: () => void
}

/** 创建空操作的消息处理器（用于参数异常时的安全返回） */
function createNoopMessageHandler(): MessageHandler {
  return { close: () => undefined }
}

/** 消息工厂函数，根据默认类型创建消息调用方法 */
function createMessage(typeFallback: string) {
  return (...args: any[]): MessageHandler => {
    const params = args[0] as MessageParams | undefined
    if (typeof params === 'string') {
      return pushToast(typeFallback, params) || createNoopMessageHandler()
    }
    if (params && typeof params === 'object') {
      return pushToast(params.type || typeFallback, params.message, params.duration) || createNoopMessageHandler()
    }
    return createNoopMessageHandler()
  }
}

/** 消息 API 接口，支持 ElMessage('text') 和 ElMessage.success('text') 两种调用方式 */
interface MessageApi {
  (params?: MessageParams, ...args: any[]): MessageHandler
  success: (params?: MessageParams, ...args: any[]) => MessageHandler
  warning: (params?: MessageParams, ...args: any[]) => MessageHandler
  info: (params?: MessageParams, ...args: any[]) => MessageHandler
  error: (params?: MessageParams, ...args: any[]) => MessageHandler
}

/* ========== 对外暴露的消息 API ========== */

/** 消息提示（轻量 Toast），兼容 Element Plus 的 ElMessage 接口 */
export const ElMessage: MessageApi = Object.assign(createMessage('info'), {
  success: createMessage('success'),
  warning: createMessage('warning'),
  info: createMessage('info'),
  error: createMessage('error')
}) as MessageApi

/** 通知提示，兼容 Element Plus 的 ElNotification 接口 */
export const ElNotification = {
  success: createMessage('success'),
  warning: createMessage('warning'),
  info: createMessage('info'),
  error: createMessage('error')
}

/** 消息弹框，使用浏览器原生 confirm/alert/prompt 实现 */
export const ElMessageBox = {
  confirm(message: string, title = '提示', _options?: Record<string, any>) {
    return new Promise<'confirm'>((resolve, reject) => {
      const ok = window.confirm(`${title}\n\n${message}`)
      if (ok) {
        resolve('confirm')
      } else {
        reject(new Error('cancel'))
      }
    })
  },
  alert(message: string, title = '提示', _options?: Record<string, any>) {
    window.alert(`${title}\n\n${message}`)
    return Promise.resolve('confirm')
  },
  prompt(message: string, title = '提示', options?: Record<string, any>) {
    return new Promise<{ value: string; action: 'confirm' }>((resolve, reject) => {
      const value = window.prompt(`${title}\n\n${message}`, options?.inputValue || '')
      if (value === null) {
        reject(new Error('cancel'))
      } else {
        resolve({ value, action: 'confirm' })
      }
    })
  }
}

/* ========== 基础 UI 组件 ========== */

/** 配置提供者组件（透传容器） */
const ElConfigProvider = defineComponent({
  name: 'ElConfigProvider',
  setup(_, { slots }) {
    return () => h('div', { class: 'el-config-provider' }, slots.default?.())
  }
})

/** 文本组件，支持 type 属性控制文字语义色 */
const ElText = defineComponent({
  name: 'ElText',
  props: { type: { type: String, default: '' } },
  setup(props, { slots }) {
    return () => h('span', { class: ['el-text', props.type ? `el-text--${props.type}` : ''] }, slots.default?.())
  }
})

/** 图标容器组件 */
const ElIcon = defineComponent({
  name: 'ElIcon',
  setup(_, { slots }) {
    return () => h('span', { class: 'el-icon', 'aria-hidden': 'true' }, slots.default?.())
  }
})

/* ========== 按钮组件 ========== */

/** 按钮组件，支持类型、尺寸、加载状态、链接模式等 */
const ElButton = defineComponent({
  props: {
    type: { type: String, default: 'default' },
    size: { type: String, default: 'default' },
    disabled: { type: Boolean, default: false },
    loading: { type: Boolean, default: false },
    link: { type: Boolean, default: false },
    text: { type: Boolean, default: false }
  },
  emits: ['click'],
  setup(props, { slots, emit, attrs }) {
    return () =>
      h(
        'button',
        {
          ...attrs,
          class: [
            'el-button',
            `el-button--${props.type}`,
            props.size !== 'default' ? `el-button--${props.size}` : '',
            props.link ? 'is-link' : '',
            props.text ? 'is-text' : '',
            props.loading ? 'is-loading' : ''
          ],
          type: (attrs.type as string) || 'button',
          disabled: props.disabled || props.loading,
          onClick: (event: MouseEvent) => emit('click', event)
        },
        [props.loading ? h('span', { class: 'el-button__spinner' }) : null, slots.default?.()]
      )
  }
})

/** 按钮组容器 */
const ElButtonGroup = defineComponent({
  name: 'ElButtonGroup',
  setup(_, { slots }) {
    return () => h('div', { class: 'el-button-group' }, slots.default?.())
  }
})

/* ========== 卡片组件 ========== */

/** 卡片组件，支持 header 插槽和 default 内容区 */
const ElCard = defineComponent({
  name: 'ElCard',
  setup(_, { slots, attrs }) {
    return () =>
      h('section', { ...attrs, class: 'el-card' }, [
        slots.header ? h('header', { class: 'el-card__header' }, slots.header()) : null,
        h('div', { class: 'el-card__body' }, slots.default?.())
      ])
  }
})

/* ========== 表单组件 ========== */

/** 表单上下文注入键，用于 ElForm 与 ElFormItem 之间的通信 */
const FormContextKey = Symbol('el-form')

/**
 * 表单组件
 *
 * 提供表单验证（validate/validateField）、重置（resetFields）、清除验证（clearValidate）等方法。
 * 通过 provide 向子组件注入表单数据模型和验证规则。
 */
const ElForm = defineComponent({
  props: {
    model: { type: Object as PropType<Record<string, any>>, default: () => ({}) },
    rules: { type: Object as PropType<FormRules>, default: () => ({}) },
    inline: { type: Boolean, default: false }
  },
  emits: ['submit'],
  setup(props, { slots, emit, expose, attrs }) {
    const initial = ref<Record<string, any>>({ ...props.model })

    const validateField: FormInstance['validateField'] = async (prop, callback) => {
      const fields = Array.isArray(prop) ? prop : [prop]
      try {
        for (const field of fields) {
          const rules = props.rules?.[field] || []
          for (const rule of rules) {
            await runRule(rule, props.model[field])
          }
        }
        callback?.()
        return true
      } catch (error) {
        const message = error instanceof Error ? error.message : '验证失败'
        callback?.(message)
        throw error
      }
    }

    const validate: FormInstance['validate'] = async (callback) => {
      const keys = Object.keys(props.rules || {})
      const fields: Record<string, string> = {}
      let valid = true

      for (const key of keys) {
        try {
          await validateField(key)
        } catch (error) {
          valid = false
          fields[key] = error instanceof Error ? error.message : '验证失败'
        }
      }

      callback?.(valid, valid ? undefined : fields)
      return valid
    }

    const resetFields: FormInstance['resetFields'] = (propsToReset) => {
      const fields =
        typeof propsToReset === 'string'
          ? [propsToReset]
          : Array.isArray(propsToReset)
            ? propsToReset
            : Object.keys(props.model || {})

      fields.forEach((key) => {
        const value = initial.value[key]
        props.model[key] = Array.isArray(value) ? [...value] : (value ?? '')
      })
    }

    const clearValidate: FormInstance['clearValidate'] = () => undefined

    provide(FormContextKey, { model: props.model, rules: props.rules })

    expose<FormInstance>({ validate, validateField, resetFields, clearValidate })

    return () =>
      h(
        'form',
        {
          ...attrs,
          class: ['el-form', props.inline ? 'el-form--inline' : ''],
          onSubmit: (event: Event) => {
            event.preventDefault()
            emit('submit', event)
          }
        },
        slots.default?.()
      )
  }
})

/** 表单项组件，包含标签和内容区 */
const ElFormItem = defineComponent({
  name: 'ElFormItem',
  props: { label: { type: String, default: '' } },
  setup(props, { slots, attrs }) {
    return () =>
      h('div', { ...attrs, class: 'el-form-item' }, [
        props.label ? h('label', { class: 'el-form-item__label' }, props.label) : null,
        h('div', { class: 'el-form-item__content' }, slots.default?.())
      ])
  }
})

/* ========== 输入框组件 ========== */

/**
 * 输入框组件
 *
 * 支持 text/password/textarea 类型，以及 clearable、showPassword 等增强功能。
 * 通过 prefix/suffix/append 插槽支持前缀、后缀和追加内容。
 */
const ElInput = defineComponent({
  props: {
    modelValue: { type: [String, Number], default: '' },
    placeholder: { type: String, default: '' },
    type: { type: String, default: 'text' },
    disabled: { type: Boolean, default: false },
    clearable: { type: Boolean, default: false },
    showPassword: { type: Boolean, default: false },
    rows: { type: Number, default: 3 }
  },
  emits: ['update:modelValue', 'change', 'input', 'blur', 'focus', 'keyup', 'keydown', 'keyup.enter', 'clear'],
  setup(props, { emit, slots, attrs }) {
    const reveal = ref(false)
    const actualType = computed(() => {
      if (props.type === 'textarea') {
        return 'textarea'
      }
      if (props.type === 'password' && props.showPassword && reveal.value) {
        return 'text'
      }
      return props.type
    })

    const onInput = (event: Event) => {
      const value = (event.target as HTMLInputElement | HTMLTextAreaElement).value
      emit('update:modelValue', value)
      emit('input', value)
      emit('change', value)
    }

    return () => {
      const field =
        actualType.value === 'textarea'
          ? h('textarea', {
              class: 'el-textarea__inner',
              value: props.modelValue as any,
              rows: props.rows,
              placeholder: props.placeholder,
              disabled: props.disabled,
              onInput
            })
          : h('input', {
              class: 'el-input__inner',
              type: actualType.value,
              value: props.modelValue as any,
              placeholder: props.placeholder,
              disabled: props.disabled,
              onInput,
              onBlur: (event: FocusEvent) => emit('blur', event),
              onFocus: (event: FocusEvent) => emit('focus', event),
              onKeyup: (event: KeyboardEvent) => {
                emit('keyup', event)
                if (event.key === 'Enter') {
                  emit('keyup.enter', event)
                }
              },
              onKeydown: (event: KeyboardEvent) => emit('keydown', event)
            })

      return h('div', { ...attrs, class: ['el-input', actualType.value === 'textarea' ? 'is-textarea' : ''] }, [
        h('div', { class: 'el-input__wrapper' }, [
          slots.prefix ? h('span', { class: 'el-input__prefix' }, slots.prefix()) : null,
          field,
          props.clearable && props.modelValue
            ? h(
                'button',
                {
                  class: 'el-input__clear',
                  type: 'button',
                  onClick: () => {
                    emit('update:modelValue', '')
                    emit('clear')
                  }
                },
                'x'
              )
            : null,
          props.showPassword && props.type === 'password'
            ? h(
                'button',
                {
                  class: 'el-input__password-toggle',
                  type: 'button',
                  onClick: () => {
                    reveal.value = !reveal.value
                  }
                },
                reveal.value ? 'Hide' : 'Show'
              )
            : null,
          slots.suffix ? h('span', { class: 'el-input__suffix' }, slots.suffix()) : null,
          slots.append ? h('span', { class: 'el-input-group__append' }, slots.append()) : null
        ])
      ])
    }
  }
})

/* ========== 选择器组件 ========== */

/** 选择器上下文注入键，用于 ElSelect 与 ElOption 之间的通信 */
const SelectContextKey = Symbol('el-select')

/** 选择器选项数据结构 */
interface SelectOptionItem {
  value: any
  label: string
  disabled: boolean
}

/** 选项组件，通过 inject 向父级 ElSelect 注册自身数据 */
const ElOption = defineComponent({
  name: 'ElOption',
  props: {
    value: { type: [String, Number, Boolean], default: '' },
    label: { type: String, default: '' },
    disabled: { type: Boolean, default: false }
  },
  setup(props) {
    const context = inject<any>(SelectContextKey, null)
    const item: SelectOptionItem = { value: props.value, label: props.label, disabled: props.disabled }
    context?.register(item)
    watch(() => [props.value, props.label, props.disabled], () => {
      item.value = props.value
      item.label = props.label
      item.disabled = props.disabled
    })
    onUnmounted(() => context?.unregister(item))
    return () => null
  }
})

/**
 * 选择器组件
 *
 * 自定义下拉菜单实现，支持单选/多选、清除、禁用等功能。
 * 通过 provide/inject 与 ElOption 子组件配合收集选项数据。
 */
const ElSelect = defineComponent({
  props: {
    modelValue: { type: [String, Number, Boolean, Array] as PropType<any>, default: '' },
    placeholder: { type: String, default: '请选择' },
    multiple: { type: Boolean, default: false },
    disabled: { type: Boolean, default: false },
    clearable: { type: Boolean, default: false }
  },
  emits: ['update:modelValue', 'change', 'clear', 'visible-change'],
  setup(props, { emit, slots, attrs }) {
    const opened = ref(false)
    const rootRef = ref<HTMLElement | null>(null)
    const options = ref<SelectOptionItem[]>([])

    provide(SelectContextKey, {
      register(item: SelectOptionItem) { options.value.push(item) },
      unregister(item: SelectOptionItem) {
        const idx = options.value.indexOf(item)
        if (idx >= 0) options.value.splice(idx, 1)
      }
    })

    const selectedLabel = computed(() => {
      if (props.multiple && Array.isArray(props.modelValue)) {
        return props.modelValue
          .map((v: any) => options.value.find((o) => o.value === v)?.label || v)
          .join(', ')
      }
      const found = options.value.find((o) => o.value === props.modelValue)
      return found ? found.label : ''
    })

    const onDocClick = (event: Event) => {
      if (!rootRef.value?.contains(event.target as Node)) {
        opened.value = false
        emit('visible-change', false)
      }
    }

    onMounted(() => document.addEventListener('mousedown', onDocClick))
    onUnmounted(() => document.removeEventListener('mousedown', onDocClick))

    const toggleOpen = () => {
      if (props.disabled) return
      opened.value = !opened.value
      emit('visible-change', opened.value)
    }

    const selectItem = (item: SelectOptionItem) => {
      if (item.disabled) return
      if (props.multiple) {
        const arr = Array.isArray(props.modelValue) ? [...props.modelValue] : []
        const idx = arr.indexOf(item.value)
        if (idx >= 0) arr.splice(idx, 1)
        else arr.push(item.value)
        emit('update:modelValue', arr)
        emit('change', arr)
      } else {
        emit('update:modelValue', item.value)
        emit('change', item.value)
        opened.value = false
        emit('visible-change', false)
      }
    }

    const isSelected = (item: SelectOptionItem) => {
      if (props.multiple && Array.isArray(props.modelValue)) {
        return props.modelValue.includes(item.value)
      }
      return props.modelValue === item.value
    }

    return () => {
      // 隐藏渲染默认插槽内容，使 ElOption 子组件能执行 setup 完成注册
      const hiddenSlot = h('div', { style: 'display:none' }, slots.default?.())

      const triggerText = selectedLabel.value || props.placeholder
      const hasValue = !isEmpty(props.modelValue)

      const trigger = h(
        'div',
        {
          class: ['el-select__wrapper', opened.value ? 'is-focused' : ''],
          onClick: toggleOpen
        },
        [
          h('span', {
            class: 'el-select__label',
            style: { color: hasValue ? 'inherit' : '#a8abb2', flex: '1', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px', lineHeight: '1' }
          }, triggerText),
          props.clearable && hasValue
            ? h('span', {
                class: 'el-select__clear',
                onClick: (event: Event) => {
                  event.stopPropagation()
                  emit('update:modelValue', props.multiple ? [] : '')
                  emit('clear')
                  opened.value = false
                  emit('visible-change', false)
                },
                style: { cursor: 'pointer', marginLeft: '4px', color: '#a8abb2', fontSize: '13px', flexShrink: '0' }
              }, '\u2715')
            : null
        ]
      )

      const dropdown = opened.value
        ? h('div', { class: 'el-select-dropdown', style: { position: 'absolute', top: '100%', left: '0', minWidth: '100%', marginTop: '4px', zIndex: '2050' } }, [
            h('div', { class: 'el-select-dropdown__list' },
              options.value.map((item) =>
                h('div', {
                  class: ['el-select-dropdown__item', isSelected(item) ? 'is-selected' : '', item.disabled ? 'is-disabled' : ''],
                  onClick: (event: Event) => { event.stopPropagation(); selectItem(item) }
                }, item.label)
              )
            )
          ])
        : null

      return h('div', { ...attrs, class: ['el-select', opened.value ? 'is-opened' : ''], ref: rootRef, style: { position: 'relative' } }, [
        hiddenSlot,
        trigger,
        dropdown
      ])
    }
  }
})

/* ========== 菜单导航组件 ========== */

/** 菜单上下文注入键 */
const MenuContextKey = Symbol('el-menu')

/** 菜单组件，支持折叠模式和路由模式 */
const ElMenu = defineComponent({
  name: 'ElMenu',
  props: { defaultActive: { type: String, default: '' }, collapse: { type: Boolean, default: false }, router: { type: Boolean, default: false } },
  setup(props, { slots, attrs }) {
    const active = ref(props.defaultActive)
    watch(() => props.defaultActive, (value) => (active.value = value))
    provide(MenuContextKey, { active, useRouter: props.router, select: (index: string) => (active.value = index) })
    return () => h('nav', { ...attrs, class: ['el-menu', props.collapse ? 'is-collapse' : ''], role: 'menu' }, slots.default?.())
  }
})

/** 菜单项组件，点击时激活并可选路由跳转 */
const ElMenuItem = defineComponent({
  name: 'ElMenuItem',
  props: { index: { type: String, required: true } },
  setup(props, { slots, attrs }) {
    const menu = inject<any>(MenuContextKey, null)
    const router = useRouter()
    return () =>
      h(
        'button',
        {
          ...attrs,
          type: 'button',
          role: 'menuitem',
          class: ['el-menu-item', menu?.active?.value === props.index ? 'is-active' : ''],
          onClick: async () => {
            menu?.select(props.index)
            if (menu?.useRouter) {
              try {
                await router.push(props.index)
              } catch {
                // ignore
              }
            }
          }
        },
        [slots.default?.(), slots.title ? h('span', { class: 'el-menu-item__title' }, slots.title()) : null]
      )
  }
})

/* ========== 下拉菜单组件 ========== */

/** 下拉菜单上下文注入键 */
const DropdownContextKey = Symbol('el-dropdown')

/** 下拉菜单组件，点击触发器显示/隐藏下拉内容 */
const ElDropdown = defineComponent({
  name: 'ElDropdown',
  emits: ['command'],
  setup(_, { slots, emit, attrs }) {
    const opened = ref(false)
    const rootRef = ref<HTMLElement | null>(null)

    provide(DropdownContextKey, {
      command: (value: string) => {
        emit('command', value)
        opened.value = false
      }
    })

    const onDocClick = (event: Event) => {
      const target = event.target as Node
      if (!rootRef.value?.contains(target)) {
        opened.value = false
      }
    }

    onMounted(() => document.addEventListener('click', onDocClick))
    onUnmounted(() => document.removeEventListener('click', onDocClick))

    return () =>
      h('div', { ...attrs, class: ['el-dropdown', opened.value ? 'is-open' : ''], ref: rootRef }, [
        h('div', { class: 'el-dropdown__trigger', onClick: (event: Event) => { event.stopPropagation(); opened.value = !opened.value } }, slots.default?.()),
        opened.value ? h('div', { class: 'el-dropdown__menu-wrap' }, slots.dropdown?.()) : null
      ])
  }
})

/** 下拉菜单面板容器 */
const ElDropdownMenu = defineComponent({
  name: 'ElDropdownMenu',
  setup(_, { slots, attrs }) {
    return () => h('div', { ...attrs, class: 'el-dropdown-menu' }, slots.default?.())
  }
})

/** 下拉菜单项，点击时触发 command 事件 */
const ElDropdownItem = defineComponent({
  name: 'ElDropdownItem',
  props: { command: { type: String, default: '' }, divided: { type: Boolean, default: false }, disabled: { type: Boolean, default: false } },
  setup(props, { slots, attrs }) {
    const dropdown = inject<any>(DropdownContextKey, null)
    return () => h('button', { ...attrs, type: 'button', class: ['el-dropdown-menu__item', props.divided ? 'is-divided' : ''], disabled: props.disabled, onClick: () => !props.disabled && dropdown?.command(props.command) }, slots.default?.())
  }
})

/* ========== 数据展示组件 ========== */

/** 头像组件，支持图片 src 或文字回退 */
const ElAvatar = defineComponent({
  name: 'ElAvatar',
  props: { size: { type: [String, Number], default: 32 }, src: { type: String, default: '' } },
  setup(props, { slots, attrs }) {
    return () => h('span', { ...attrs, class: 'el-avatar', style: { width: `${props.size}px`, height: `${props.size}px` } }, props.src ? h('img', { src: props.src, alt: 'avatar' }) : slots.default?.() || 'U')
  }
})

/* ========== 开关组件 ========== */

/** 开关组件，支持 v-model 双向绑定和禁用状态 */
const ElSwitch = defineComponent({
  name: 'ElSwitch',
  props: { modelValue: { type: Boolean, default: false }, disabled: { type: Boolean, default: false } },
  emits: ['update:modelValue', 'change'],
  setup(props, { emit, attrs }) {
    return () => h('button', { ...attrs, type: 'button', class: ['el-switch', props.modelValue ? 'is-checked' : '', props.disabled ? 'is-disabled' : ''], onClick: () => { if (!props.disabled) { const value = !props.modelValue; emit('update:modelValue', value); emit('change', value) } } }, h('span', { class: 'el-switch__core' }))
  }
})

/* ========== 对话框组件 ========== */

/** 模态对话框组件，支持标题、宽度、点击遮罩关闭、header/footer 插槽 */
const ElDialog = defineComponent({
  name: 'ElDialog',
  props: { modelValue: { type: Boolean, default: false }, title: { type: String, default: '' }, width: { type: [String, Number], default: '560px' }, closeOnClickModal: { type: Boolean, default: true } },
  emits: ['update:modelValue', 'close', 'open', 'opened', 'closed'],
  setup(props, { emit, slots, attrs }) {
    watch(() => props.modelValue, (visible) => { emit(visible ? 'open' : 'close'); nextTick(() => emit(visible ? 'opened' : 'closed')) }, { immediate: true })
    const close = () => { emit('update:modelValue', false); emit('close') }
    return () => props.modelValue ? h('div', { ...attrs, class: 'el-dialog-wrapper' }, [
      h('div', { class: 'el-overlay', onClick: () => { if (props.closeOnClickModal) { close() } } }),
      h('div', { class: 'el-dialog', role: 'dialog', style: { width: typeof props.width === 'number' ? `${props.width}px` : props.width } }, [
        h('header', { class: 'el-dialog__header' }, [slots.header ? slots.header() : h('span', { class: 'el-dialog__title' }, props.title), h('button', { class: 'el-dialog__close', type: 'button', onClick: close }, 'x')]),
        h('section', { class: 'el-dialog__body' }, slots.default?.()),
        slots.footer ? h('footer', { class: 'el-dialog__footer' }, slots.footer()) : null
      ])
    ]) : null
  }
})

/* ========== 简单占位组件工厂 ========== */

/**
 * 创建简单的透传组件
 *
 * 用于那些只需要提供基础 DOM 结构和 CSS 类名的组件（如 ElEmpty、ElTag 等），
 * 避免为每个组件编写重复的 defineComponent 模板代码。
 *
 * @param name - 组件注册名称
 * @param tag - 渲染的 HTML 标签，默认 'div'
 * @param className - CSS 类名，默认由组件名自动转换为 kebab-case
 */
function simple(name: string, tag = 'div', className = '') {
  return defineComponent({
    name,
    setup(_, { slots, attrs }) {
      return () => h(tag, { ...attrs, class: className || toKebab(name) }, slots.default?.())
    }
  })
}

/* 通过工厂函数批量生成的简单组件 */
const ElEmpty = simple('ElEmpty', 'div', 'el-empty')
const ElBadge = simple('ElBadge', 'span', 'el-badge')
const ElBreadcrumb = simple('ElBreadcrumb', 'nav', 'el-breadcrumb')
const ElBreadcrumbItem = simple('ElBreadcrumbItem', 'span', 'el-breadcrumb-item')
const ElDatePicker = simple('ElDatePicker', 'input', 'el-date-picker')
const ElDescriptions = simple('ElDescriptions', 'div', 'el-descriptions')
const ElDescriptionsItem = simple('ElDescriptionsItem', 'div', 'el-descriptions-item')
const ElDivider = simple('ElDivider', 'div', 'el-divider')
const ElImage = simple('ElImage', 'img', 'el-image')
const ElInputNumber = simple('ElInputNumber', 'div', 'el-input-number')
const ElLink = simple('ElLink', 'a', 'el-link')
const ElOptionGroup = simple('ElOptionGroup', 'optgroup', 'el-option-group')
const ElPageHeader = simple('ElPageHeader', 'header', 'el-page-header')
const ElPopover = simple('ElPopover', 'span', 'el-popover')
const ElProgress = simple('ElProgress', 'div', 'el-progress')
const ElRadio = simple('ElRadio', 'label', 'el-radio')
const ElRadioButton = simple('ElRadioButton', 'label', 'el-radio-button')
const ElRadioGroup = simple('ElRadioGroup', 'div', 'el-radio-group')
const ElResult = simple('ElResult', 'section', 'el-result')

/* ========== 栅格布局组件 ========== */

/**
 * 行组件（ElRow）
 *
 * 基于 Flexbox 实现的栅格行容器，支持：
 * - gutter: 列间距（通过 provide 传递给子 ElCol）
 * - justify: 水平对齐方式
 * - align: 垂直对齐方式
 */
const ElRow = defineComponent({
  name: 'ElRow',
  props: {
    gutter: { type: Number, default: 0 },
    justify: { type: String, default: 'start' },
    align: { type: String, default: 'top' },
    tag: { type: String, default: 'div' }
  },
  setup(props, { slots }) {
    provide('ElRowGutter', computed(() => props.gutter))
    return () => h(props.tag, {
      class: 'el-row',
      style: {
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: props.justify === 'start' ? 'flex-start' :
                         props.justify === 'end' ? 'flex-end' :
                         props.justify === 'center' ? 'center' :
                         props.justify === 'space-between' ? 'space-between' :
                         props.justify === 'space-around' ? 'space-around' :
                         props.justify === 'space-evenly' ? 'space-evenly' : 'flex-start',
        alignItems: props.align === 'top' ? 'flex-start' :
                    props.align === 'middle' ? 'center' :
                    props.align === 'bottom' ? 'flex-end' : 'flex-start',
        marginLeft: props.gutter ? `-${props.gutter / 2}px` : undefined,
        marginRight: props.gutter ? `-${props.gutter / 2}px` : undefined
      }
    }, slots.default?.())
  }
})

/**
 * 列组件（ElCol）
 *
 * 24 等分栅格系统的列组件，通过 inject 获取父级 ElRow 的 gutter 值。
 * 支持 span（占据列数）和 offset（左侧偏移列数）。
 */
const ElCol = defineComponent({
  props: {
    span: { type: Number, default: 24 },
    offset: { type: Number, default: 0 },
    push: { type: Number, default: 0 },
    pull: { type: Number, default: 0 },
    tag: { type: String, default: 'div' }
  },
  setup(props, { slots }) {
    const gutter = inject<ReturnType<typeof computed<number>>>('ElRowGutter', computed(() => 0))
    return () => {
      const width = `${(props.span / 24) * 100}%`
      const marginLeft = props.offset > 0 ? `${(props.offset / 24) * 100}%` : undefined
      const g = gutter.value
      return h(props.tag, {
        class: ['el-col', `el-col-${props.span}`],
        style: {
          maxWidth: width,
          flex: `0 0 ${width}`,
          paddingLeft: g ? `${g / 2}px` : undefined,
          paddingRight: g ? `${g / 2}px` : undefined,
          marginLeft,
          boxSizing: 'border-box'
        }
      }, slots.default?.())
    }
  }
})
const ElScrollbar = simple('ElScrollbar', 'div', 'el-scrollbar')
const ElSlider = simple('ElSlider', 'input', 'el-slider')
const ElSpace = simple('ElSpace', 'div', 'el-space')
const ElStatistic = simple('ElStatistic', 'div', 'el-statistic')
const ElTable = simple('ElTable', 'div', 'el-table')
/** 表格列组件（占位，不渲染 DOM） */
const ElTableColumn = defineComponent({
  name: 'ElTableColumn',
  setup() {
    return () => null
  }
})
const ElTabs = simple('ElTabs', 'div', 'el-tabs')
const ElTabPane = simple('ElTabPane', 'div', 'el-tab-pane')
const ElTag = simple('ElTag', 'span', 'el-tag')
const ElTimeline = simple('ElTimeline', 'ul', 'el-timeline')
const ElTimelineItem = simple('ElTimelineItem', 'li', 'el-timeline-item')
const ElTooltip = simple('ElTooltip', 'span', 'el-tooltip')
const ElTransfer = simple('ElTransfer', 'div', 'el-transfer')
const ElUpload = simple('ElUpload', 'label', 'el-upload')
const ElCheckbox = simple('ElCheckbox', 'label', 'el-checkbox')
const ElCheckboxGroup = simple('ElCheckboxGroup', 'div', 'el-checkbox-group')
const ElCollapse = simple('ElCollapse', 'div', 'el-collapse')
const ElCollapseItem = simple('ElCollapseItem', 'div', 'el-collapse-item')
const ElCollapseTransition = simple('ElCollapseTransition', 'div', 'el-collapse-transition')
const ElPagination = simple('ElPagination', 'div', 'el-pagination')

/* ========== 组件注册表 ========== */

/** 所有兼容组件的集合，用于 Vue 插件全局注册 */
const components: Record<string, any> = {
  ElAlert: simple('ElAlert', 'div', 'el-alert'),
  ElAvatar,
  ElBadge,
  ElBreadcrumb,
  ElBreadcrumbItem,
  ElButton,
  ElButtonGroup,
  ElCard,
  ElCheckbox,
  ElCheckboxGroup,
  ElCol,
  ElCollapse,
  ElCollapseItem,
  ElCollapseTransition,
  ElConfigProvider,
  ElDatePicker,
  ElDescriptions,
  ElDescriptionsItem,
  ElDialog,
  ElDivider,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElImage,
  ElInput,
  ElInputNumber,
  ElLink,
  ElMenu,
  ElMenuItem,
  ElOption,
  ElOptionGroup,
  ElPageHeader,
  ElPagination,
  ElPopover,
  ElProgress,
  ElRadio,
  ElRadioButton,
  ElRadioGroup,
  ElResult,
  ElRow,
  ElScrollbar,
  ElSelect,
  ElSlider,
  ElSpace,
  ElStatistic,
  ElSwitch,
  ElTabPane,
  ElTable,
  ElTableColumn,
  ElTabs,
  ElTag,
  ElText,
  ElTimeline,
  ElTimelineItem,
  ElTooltip,
  ElTransfer,
  ElUpload
}

/* ========== Vue 插件安装器 ========== */

/**
 * Element Plus 兼容层插件
 *
 * 安装时执行以下操作：
 * 1. 全局注册所有组件（同时注册 PascalCase 和 kebab-case 两种名称）
 * 2. 挂载 $message/$notify/$msgbox 到全局属性
 * 3. 注册 v-loading 指令
 */
const ElementPlusCompat = {
  install(app: App) {
    Object.entries(components).forEach(([name, component]) => {
      app.component(name, component)
      app.component(toKebab(name), component)
    })

    app.config.globalProperties.$message = ElMessage
    app.config.globalProperties.$notify = ElNotification
    app.config.globalProperties.$msgbox = ElMessageBox

    app.directive('loading', {
      mounted(el, binding) {
        if (binding.value) {
          el.classList.add('el-loading-parent--relative')
        }
      },
      updated(el, binding) {
        if (binding.value) {
          el.classList.add('el-loading-parent--relative')
        } else {
          el.classList.remove('el-loading-parent--relative')
        }
      }
    })
  }
}

/* ========== 模块导出 ========== */

export default ElementPlusCompat

export {
  ElConfigProvider,
  ElForm,
  ElFormItem,
  ElInput,
  ElButton
}
