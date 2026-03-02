/**
 * 项目状态管理（Pinia Store）
 *
 * 管理 UI 自动化测试项目的列表、当前选中项目、
 * 项目统计信息等状态数据。
 */

import { defineStore } from 'pinia'

import { uiProjectApi } from '../api/project'
import type { UiProject, UiProjectCreate, UiProjectStatistics } from '../types/project'

/** 项目 Store 的状态类型定义 */
interface ProjectState {
  /** 项目列表 */
  projects: UiProject[]
  /** 当前查看的项目详情 */
  currentProject: UiProject | null
  /** 当前项目的统计数据 */
  projectStatistics: UiProjectStatistics | null
  /** 列表加载状态 */
  loading: boolean
  /** 列表总数（用于分页） */
  total: number
}

export const useUiProjectStore = defineStore('uiProject', {
  state: (): ProjectState => ({
    projects: [],
    currentProject: null,
    projectStatistics: null,
    loading: false,
    total: 0
  }),

  getters: {
    /** 将项目列表转换为下拉选项格式（label + value） */
    projectOptions: (state) => {
      return state.projects.map(project => ({
        label: project.name,
        value: project.id
      }))
    },

    /** 筛选出已启用的项目 */
    activeProjects: (state) => {
      return state.projects.filter(p => p.is_active)
    }
  },

  actions: {
    /** 获取项目列表（支持分页和筛选参数） */
    async fetchProjects(params?: any) {
      this.loading = true
      try {
        const response = await uiProjectApi.getProjects(params)
        this.projects = response.results
        this.total = response.count
        return response
      } catch (error) {
        console.error('Failed to fetch UI projects:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /** 获取单个项目详情并设为当前项目 */
    async fetchProject(id: number) {
      this.loading = true
      try {
        const project = await uiProjectApi.getProject(id)
        this.currentProject = project
        return project
      } catch (error) {
        console.error('Failed to fetch UI project:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /** 创建项目并插入列表头部 */
    async createProject(data: UiProjectCreate) {
      try {
        const project = await uiProjectApi.createProject(data)
        this.projects.unshift(project)
        this.total += 1
        return project
      } catch (error) {
        console.error('Failed to create UI project:', error)
        throw error
      }
    },

    /** 更新项目信息并同步列表和当前项目 */
    async updateProject(id: number, data: Partial<UiProjectCreate>) {
      try {
        const updatedProject = await uiProjectApi.updateProject(id, data)
        const index = this.projects.findIndex(p => p.id === id)
        if (index !== -1) {
          this.projects[index] = updatedProject
        }
        if (this.currentProject?.id === id) {
          this.currentProject = updatedProject
        }
        return updatedProject
      } catch (error) {
        console.error('Failed to update UI project:', error)
        throw error
      }
    },

    /** 删除项目并从列表中移除 */
    async deleteProject(id: number) {
      try {
        await uiProjectApi.deleteProject(id)
        this.projects = this.projects.filter(p => p.id !== id)
        this.total -= 1
        if (this.currentProject?.id === id) {
          this.currentProject = null
        }
      } catch (error) {
        console.error('Failed to delete UI project:', error)
        throw error
      }
    },

    /** 获取项目统计信息（用例数、执行数、成功率等） */
    async fetchProjectStatistics(id: number) {
      try {
        const statistics = await uiProjectApi.getProjectStatistics(id)
        this.projectStatistics = statistics
        return statistics
      } catch (error) {
        console.error('Failed to fetch project statistics:', error)
        throw error
      }
    },

    /** 清除当前项目和统计数据（离开项目详情页时调用） */
    clearCurrentProject() {
      this.currentProject = null
      this.projectStatistics = null
    }
  }
})
