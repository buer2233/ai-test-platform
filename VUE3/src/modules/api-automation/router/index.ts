/**
 * 路由配置
 *
 * 定义 API 自动化测试模块的所有路由，包括：
 * - 登录页（无需认证）
 * - 主布局下的子路由（需认证）：仪表盘、项目、集合、测试用例、
 *   环境、HTTP 执行器、报告、数据驱动、回收站等
 *
 * 所有视图组件均采用懒加载，按需加载以优化首屏性能。
 */

import type { RouteRecordRaw } from 'vue-router'

// ==================== 懒加载视图组件 ====================

const Layout = () => import('../components/Layout/index.vue')
const Dashboard = () => import('../views/Dashboard/index.vue')
const ProjectList = () => import('../views/Project/ProjectList.vue')
const ProjectDetail = () => import('../views/Project/ProjectDetail.vue')
const CollectionList = () => import('../views/Collection/CollectionList.vue')
const CollectionDetail = () => import('../views/Collection/CollectionDetail.vue')
const TestCaseList = () => import('../views/TestCase/TestCaseList.vue')
const TestCaseDetail = () => import('../views/TestCase/TestCaseDetail.vue')
const TestCaseCreate = () => import('../views/TestCase/TestCaseCreate.vue')
const EnvironmentList = () => import('../views/Environment/EnvironmentList.vue')
const ReportList = () => import('../views/Reports/ReportList.vue')
const ReportDetail = () => import('../views/Reports/ReportDetail.vue')
const ReportViewer = () => import('../components/EnhancedReportViewer.vue')
const DataDrivenConfig = () => import('../components/DataDrivenConfig.vue')
const HttpExecutor = () => import('../views/HttpExecutor/HttpExecutor.vue')
const HttpExecutionRecords = () => import('../views/HttpExecutor/HttpExecutionRecords.vue')
const RecycleBin = () => import('../views/RecycleBin/index.vue')
const Login = () => import('../views/Auth/Login.vue')

// ==================== 路由表 ====================

export const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: {
          title: '仪表盘',
          icon: 'odometer'
        }
      },
      {
        path: 'projects',
        name: 'ProjectList',
        component: ProjectList,
        meta: {
          title: '项目管理',
          icon: 'folder-opened'
        }
      },
      {
        path: 'projects/:id',
        name: 'ProjectDetail',
        component: ProjectDetail,
        meta: {
          title: '项目详情',
          hidden: true
        },
        props: true
      },
      {
        path: 'collections',
        name: 'CollectionList',
        component: CollectionList,
        meta: {
          title: '集合管理',
          icon: 'collection'
        }
      },
      {
        path: 'collections/:id',
        name: 'CollectionDetail',
        component: CollectionDetail,
        meta: {
          title: '集合详情',
          hidden: true
        },
        props: true
      },
      {
        path: 'test-cases',
        name: 'TestCaseList',
        component: TestCaseList,
        meta: {
          title: '接口测试',
          icon: 'document-checked'
        }
      },
      {
        path: 'test-cases/create',
        name: 'TestCaseCreate',
        component: TestCaseCreate,
        meta: {
          title: '创建接口',
          hidden: true
        }
      },
      {
        path: 'test-cases/:id',
        name: 'TestCaseDetail',
        component: TestCaseDetail,
        meta: {
          title: '接口详情',
          hidden: true
        },
        props: true
      },
      {
        path: 'test-cases/:id/edit',
        name: 'TestCaseEdit',
        component: TestCaseCreate,
        meta: {
          title: '编辑接口',
          hidden: true
        },
        props: (route) => ({
          id: Number(route.params.id),
          isEdit: true
        })
      },
      {
        path: 'reports',
        name: 'ReportList',
        component: ReportList,
        meta: {
          title: '测试报告',
          icon: 'document'
        }
      },
      {
        path: 'reports/:id',
        name: 'ReportDetail',
        component: ReportDetail,
        meta: {
          title: '报告详情',
          hidden: true
        },
        props: true
      },
      {
        path: 'data-driven',
        name: 'DataDrivenConfig',
        component: DataDrivenConfig,
        meta: {
          title: '数据驱动测试',
          icon: 'data-analysis'
        }
      },
      {
        path: 'environments',
        name: 'EnvironmentList',
        component: EnvironmentList,
        meta: {
          title: '环境管理',
          icon: 'setting'
        }
      },
      {
        path: 'http-executor',
        name: 'HttpExecutor',
        component: HttpExecutor,
        meta: {
          title: 'HTTP执行器',
          icon: 'connection'
        }
      },
      {
        path: 'http-execution-records',
        name: 'HttpExecutionRecords',
        component: HttpExecutionRecords,
        meta: {
          title: '执行记录',
          icon: 'tickets'
        }
      },
      {
        path: 'recycle-bin',
        name: 'RecycleBin',
        component: RecycleBin,
        meta: {
          title: '回收站',
          icon: 'delete'
        }
      }
    ]
  }
]