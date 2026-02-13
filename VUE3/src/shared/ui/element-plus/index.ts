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

type RuleValidator = (
  rule: Record<string, any>,
  value: unknown,
  callback: (error?: Error) => void
) => void | Promise<void>

export type FormRules = Record<string, Array<Record<string, any> & { validator?: RuleValidator }>>

export interface FormInstance {
  validate: (callback?: (valid: boolean, fields?: Record<string, string>) => void) => Promise<boolean>
  validateField: (prop: string | string[], callback?: (errorMessage?: string) => void) => Promise<boolean>
  resetFields: (props?: string | string[]) => void
  clearValidate: (props?: string | string[]) => void
}

function toKebab(input: string): string {
  return input.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase()
}

function isEmpty(value: unknown): boolean {
  if (Array.isArray(value)) {
    return value.length === 0
  }
  return value === '' || value === null || value === undefined
}

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

const ToastContainerId = '__el_compat_toasts__'

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

type MessageParams = string | { message: string; type?: string; duration?: number }

interface MessageHandler {
  close: () => void
}

function createNoopMessageHandler(): MessageHandler {
  return { close: () => undefined }
}

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

interface MessageApi {
  (params?: MessageParams, ...args: any[]): MessageHandler
  success: (params?: MessageParams, ...args: any[]) => MessageHandler
  warning: (params?: MessageParams, ...args: any[]) => MessageHandler
  info: (params?: MessageParams, ...args: any[]) => MessageHandler
  error: (params?: MessageParams, ...args: any[]) => MessageHandler
}

export const ElMessage: MessageApi = Object.assign(createMessage('info'), {
  success: createMessage('success'),
  warning: createMessage('warning'),
  info: createMessage('info'),
  error: createMessage('error')
}) as MessageApi

export const ElNotification = {
  success: createMessage('success'),
  warning: createMessage('warning'),
  info: createMessage('info'),
  error: createMessage('error')
}

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

const ElConfigProvider = defineComponent({
  name: 'ElConfigProvider',
  setup(_, { slots }) {
    return () => h('div', { class: 'el-config-provider' }, slots.default?.())
  }
})

const ElText = defineComponent({
  name: 'ElText',
  props: { type: { type: String, default: '' } },
  setup(props, { slots }) {
    return () => h('span', { class: ['el-text', props.type ? `el-text--${props.type}` : ''] }, slots.default?.())
  }
})

const ElIcon = defineComponent({
  name: 'ElIcon',
  setup(_, { slots }) {
    return () => h('span', { class: 'el-icon', 'aria-hidden': 'true' }, slots.default?.())
  }
})

const ElButton = defineComponent({
  name: 'ElButton',
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

const ElButtonGroup = defineComponent({
  name: 'ElButtonGroup',
  setup(_, { slots }) {
    return () => h('div', { class: 'el-button-group' }, slots.default?.())
  }
})

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

const FormContextKey = Symbol('el-form')

const ElForm = defineComponent({
  name: 'ElForm',
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

const ElInput = defineComponent({
  name: 'ElInput',
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

const SelectContextKey = Symbol('el-select')

const ElOption = defineComponent({
  name: 'ElOption',
  props: {
    value: { type: [String, Number, Boolean], default: '' },
    label: { type: String, default: '' },
    disabled: { type: Boolean, default: false }
  },
  setup(props, { slots }) {
    const context = inject<any>(SelectContextKey, null)
    if (context?.native) {
      return () => h('option', { value: props.value as any, disabled: props.disabled }, slots.default?.() || props.label)
    }
    return () => null
  }
})

const ElSelect = defineComponent({
  name: 'ElSelect',
  props: {
    modelValue: { type: [String, Number, Boolean, Array] as PropType<any>, default: '' },
    placeholder: { type: String, default: '请选择' },
    multiple: { type: Boolean, default: false },
    disabled: { type: Boolean, default: false },
    clearable: { type: Boolean, default: false }
  },
  emits: ['update:modelValue', 'change', 'clear', 'visible-change'],
  setup(props, { emit, slots, attrs }) {
    provide(SelectContextKey, { native: true })
    return () =>
      h('div', { ...attrs, class: 'el-select' }, [
        h(
          'select',
          {
            class: 'el-select__wrapper',
            value: props.modelValue as any,
            multiple: props.multiple,
            disabled: props.disabled,
            onChange: (event: Event) => {
              const target = event.target as HTMLSelectElement
              if (props.multiple) {
                const values = Array.from(target.selectedOptions).map((item) => item.value)
                emit('update:modelValue', values)
                emit('change', values)
              } else {
                emit('update:modelValue', target.value)
                emit('change', target.value)
              }
            },
            onFocus: () => emit('visible-change', true),
            onBlur: () => emit('visible-change', false)
          },
          [!props.multiple ? h('option', { value: '', disabled: true, hidden: true }, props.placeholder) : null, slots.default?.()]
        ),
        props.clearable && !isEmpty(props.modelValue)
          ? h(
              'button',
              {
                class: 'el-select__clear',
                type: 'button',
                onClick: () => {
                  emit('update:modelValue', props.multiple ? [] : '')
                  emit('clear')
                }
              },
              'x'
            )
          : null
      ])
  }
})

const MenuContextKey = Symbol('el-menu')

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

const DropdownContextKey = Symbol('el-dropdown')

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

const ElDropdownMenu = defineComponent({
  name: 'ElDropdownMenu',
  setup(_, { slots, attrs }) {
    return () => h('div', { ...attrs, class: 'el-dropdown-menu' }, slots.default?.())
  }
})

const ElDropdownItem = defineComponent({
  name: 'ElDropdownItem',
  props: { command: { type: String, default: '' }, divided: { type: Boolean, default: false }, disabled: { type: Boolean, default: false } },
  setup(props, { slots, attrs }) {
    const dropdown = inject<any>(DropdownContextKey, null)
    return () => h('button', { ...attrs, type: 'button', class: ['el-dropdown-menu__item', props.divided ? 'is-divided' : ''], disabled: props.disabled, onClick: () => !props.disabled && dropdown?.command(props.command) }, slots.default?.())
  }
})

const ElAvatar = defineComponent({
  name: 'ElAvatar',
  props: { size: { type: [String, Number], default: 32 }, src: { type: String, default: '' } },
  setup(props, { slots, attrs }) {
    return () => h('span', { ...attrs, class: 'el-avatar', style: { width: `${props.size}px`, height: `${props.size}px` } }, props.src ? h('img', { src: props.src, alt: 'avatar' }) : slots.default?.() || 'U')
  }
})

const ElSwitch = defineComponent({
  name: 'ElSwitch',
  props: { modelValue: { type: Boolean, default: false }, disabled: { type: Boolean, default: false } },
  emits: ['update:modelValue', 'change'],
  setup(props, { emit, attrs }) {
    return () => h('button', { ...attrs, type: 'button', class: ['el-switch', props.modelValue ? 'is-checked' : '', props.disabled ? 'is-disabled' : ''], onClick: () => { if (!props.disabled) { const value = !props.modelValue; emit('update:modelValue', value); emit('change', value) } } }, h('span', { class: 'el-switch__core' }))
  }
})

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

function simple(name: string, tag = 'div', className = '') {
  return defineComponent({
    name,
    setup(_, { slots, attrs }) {
      return () => h(tag, { ...attrs, class: className || toKebab(name) }, slots.default?.())
    }
  })
}

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
const ElRow = simple('ElRow', 'div', 'el-row')
const ElCol = simple('ElCol', 'div', 'el-col')
const ElScrollbar = simple('ElScrollbar', 'div', 'el-scrollbar')
const ElSlider = simple('ElSlider', 'input', 'el-slider')
const ElSpace = simple('ElSpace', 'div', 'el-space')
const ElStatistic = simple('ElStatistic', 'div', 'el-statistic')
const ElTable = simple('ElTable', 'div', 'el-table')
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

export default ElementPlusCompat

export {
  ElConfigProvider,
  ElForm,
  ElFormItem,
  ElInput,
  ElButton
}
