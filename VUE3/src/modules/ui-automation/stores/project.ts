import { defineStore } from 'pinia'
import { uiProjectApi } from '../api/project'
import type { UiProject, UiProjectCreate, UiProjectStatistics } from '../types/project'

interface ProjectState {
  projects: UiProject[]
  currentProject: UiProject | null
  projectStatistics: UiProjectStatistics | null
  loading: boolean
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
    projectOptions: (state) => {
      return state.projects.map(project => ({
        label: project.name,
        value: project.id
      }))
    },

    activeProjects: (state) => {
      return state.projects.filter(p => p.is_active)
    }
  },

  actions: {
    // 获取项目列表
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

    // 获取单个项目
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

    // 创建项目
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

    // 更新项目
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

    // 删除项目
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

    // 获取项目统计信息
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

    // 清除当前项目
    clearCurrentProject() {
      this.currentProject = null
      this.projectStatistics = null
    }
  }
})
