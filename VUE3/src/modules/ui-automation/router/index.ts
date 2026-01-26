import type { RouteRecordRaw } from 'vue-router'

// 导入布局组件
const Layout = () => import('../components/UiLayout/index.vue')

// 懒加载视图组件
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
        component: TestCaseCreate,
        meta: {
          title: '编辑UI用例',
          hidden: true
        },
        props: (route) => ({
          id: Number(route.params.id),
          isEdit: true
        })
      },
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
