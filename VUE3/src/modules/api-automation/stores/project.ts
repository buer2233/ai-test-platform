/**
 * 项目 Store
 *
 * 管理项目的状态：项目列表、当前选中项目、加载状态等。
 * 提供项目的增删改查和克隆操作。
 */

import { defineStore } from 'pinia'
import { projectApi } from '../api/project'
import type { ApiProject, ApiProjectCreate } from '../types/project'

/** 项目状态接口 */
interface ProjectState {
  projects: ApiProject[]
  currentProject: ApiProject | null
  loading: boolean
  total: number
}

export const useProjectStore = defineStore('project', {
  state: (): ProjectState => ({
    projects: [],
    currentProject: null,
    loading: false,
    total: 0
  }),

  getters: {
    /** 转换为下拉选项格式（用于表单选择器） */
    projectOptions: (state) => {
      return state.projects.map(project => ({
        label: project.name,
        value: project.id
      }))
    }
  },

  actions: {
    /** 获取项目列表 */
    async fetchProjects(params?: any) {
      this.loading = true
      try {
        const response = await projectApi.getProjects(params)
        this.projects = response.results
        this.total = response.count
        return response
      } catch (error) {
        console.error('获取项目列表失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /** 获取单个项目详情 */
    async fetchProject(id: number) {
      this.loading = true
      try {
        const project = await projectApi.getProject(id)
        this.currentProject = project
        return project
      } catch (error) {
        console.error('获取项目详情失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /** 创建项目，并将新项目插入列表顶部 */
    async createProject(data: ApiProjectCreate) {
      try {
        const project = await projectApi.createProject(data)
        this.projects.unshift(project)
        this.total += 1
        return project
      } catch (error) {
        console.error('创建项目失败:', error)
        throw error
      }
    },

    /** 更新项目信息，同步更新列表和当前选中项 */
    async updateProject(id: number, data: Partial<ApiProjectCreate>) {
      try {
        const updatedProject = await projectApi.updateProject(id, data)
        const index = this.projects.findIndex(p => p.id === id)
        if (index !== -1) {
          this.projects[index] = updatedProject
        }
        if (this.currentProject?.id === id) {
          this.currentProject = updatedProject
        }
        return updatedProject
      } catch (error) {
        console.error('更新项目失败:', error)
        throw error
      }
    },

    /** 删除项目，同步从列表中移除 */
    async deleteProject(id: number) {
      try {
        await projectApi.deleteProject(id)
        this.projects = this.projects.filter(p => p.id !== id)
        this.total -= 1
        if (this.currentProject?.id === id) {
          this.currentProject = null
        }
      } catch (error) {
        console.error('删除项目失败:', error)
        throw error
      }
    },

    /** 克隆项目（包括其下所有集合和测试用例） */
    async cloneProject(id: number, name: string) {
      try {
        const clonedProject = await projectApi.cloneProject(id, { name })
        this.projects.unshift(clonedProject)
        this.total += 1
        return clonedProject
      } catch (error) {
        console.error('克隆项目失败:', error)
        throw error
      }
    },

    /** 清除当前选中的项目 */
    clearCurrentProject() {
      this.currentProject = null
    }
  }
})