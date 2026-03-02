/**
 * UI自动化测试模块路由配置
 *
 * 所有路由挂载在 /ui-automation 路径下，使用 UiLayout 作为布局容器。
 * 视图组件均采用懒加载方式引入，以优化首屏加载速度。
 *
 * 路由结构：
 * - /ui-automation/projects          项目列表
 * - /ui-automation/projects/:id      项目详情
 * - /ui-automation/test-cases        测试用例列表
 * - /ui-automation/test-cases/create 创建测试用例
 * - /ui-automation/test-cases/:id    用例详情
 * - /ui-automation/test-cases/:id/edit 编辑用例
 * - /ui-automation/executions        执行记录列表
 * - /ui-automation/executions/:id    执行监控
 * - /ui-automation/reports           报告列表
 * - /ui-automation/reports/:id       报告详情
 */

import type { RouteRecordRaw } from 'vue-router'

/* ---------- 布局组件（懒加载） ---------- */
const Layout = () => import('../components/UiLayout/index.vue')

/* ---------- 视图组件（懒加载） ---------- */
const ProjectList = () => import('../views/Project/ProjectList.vue')
const ProjectDetail = () => import('../views/Project/ProjectDetail.vue')
const TestCaseList = () => import('../views/TestCase/TestCaseList.vue')
const TestCaseDetail = () => import('../views/TestCase/TestCaseDetail.vue')
const TestCaseCreate = () => import('../views/TestCase/TestCaseCreate.vue')
const ExecutionList = () => import('../views/Execution/ExecutionList.vue')
const ExecutionMonitor = () => import('../views/Execution/ExecutionMonitor.vue')
const ReportList = () => import('../views/Report/ReportList.vue')
const ReportDetail = () => import('../views/Report/ReportDetail.vue')

export const routes: RouteRecordRaw[] = [
  {
    path: '/ui-automation',
    component: Layout,
    redirect: '/ui-automation/projects',
    meta: {
      requiresAuth: true,
      title: 'UI自动化测试'
    },
    children: [
      /* ---- 项目管理 ---- */
      {
        path: 'projects',
        name: 'UiProjectList',
        component: ProjectList,
        meta: {
          title: 'UI测试项目',
          icon: 'folder-opened'
        }
      },
      {
        path: 'projects/:id',
        name: 'UiProjectDetail',
        component: ProjectDetail,
        meta: {
          title: '项目详情',
          hidden: true
        },
        props: true
      },

      /* ---- 测试用例 ---- */
      {
        path: 'test-cases',
        name: 'UiTestCaseList',
        component: TestCaseList,
        meta: {
          title: 'UI测试用例',
          icon: 'document-checked'
        }
      },
      {
        path: 'test-cases/create',
        name: 'UiTestCaseCreate',
        component: TestCaseCreate,
        meta: {
          title: '创建UI用例',
          hidden: true
        }
      },
      {
        path: 'test-cases/:id',
        name: 'UiTestCaseDetail',
        component: TestCaseDetail,
        meta: {
          title: '用例详情',
          hidden: true
        },
        props: true
      },
      {
        path: 'test-cases/:id/edit',
        name: 'UiTestCaseEdit',
        component: TestCaseCreate,  // 复用创建页组件，通过 isEdit prop 区分模式
        meta: {
          title: '编辑UI用例',
          hidden: true
        },
        props: (route) => ({
          id: Number(route.params.id),
          isEdit: true
        })
      },

      /* ---- 执行记录 ---- */
      {
        path: 'executions',
        name: 'UiExecutionList',
        component: ExecutionList,
        meta: {
          title: '执行记录',
          icon: 'tickets'
        }
      },
      {
        path: 'executions/:id',
        name: 'UiExecutionMonitor',
        component: ExecutionMonitor,
        meta: {
          title: '执行监控',
          hidden: true
        },
        props: true
      },

      /* ---- 测试报告 ---- */
      {
        path: 'reports',
        name: 'UiReportList',
        component: ReportList,
        meta: {
          title: '测试报告',
          icon: 'document'
        }
      },
      {
        path: 'reports/:id',
        name: 'UiReportDetail',
        component: ReportDetail,
        meta: {
          title: '报告详情',
          hidden: true
        },
        props: true
      }
    ]
  }
]
