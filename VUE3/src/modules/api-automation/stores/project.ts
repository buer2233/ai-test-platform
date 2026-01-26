import { defineStore } from 'pinia'
import { projectApi } from '../api/project'
import type { ApiProject, ApiProjectCreate } from '../types/project'

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
    projectOptions: (state) => {
      return state.projects.map(project => ({
        label: project.name,
        value: project.id
      }))
    }
  },

  actions: {
    // 获取项目列表
    async fetchProjects(params?: any) {
      this.loading = true
      try {
        const response = await projectApi.getProjects(params)
        this.projects = response.results
        this.total = response.count
        return response
      } catch (error) {
        console.error('Failed to fetch projects:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取单个项目
    async fetchProject(id: number) {
      this.loading = true
      try {
        const project = await projectApi.getProject(id)
        this.currentProject = project
        return project
      } catch (error) {
        console.error('Failed to fetch project:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    // 创建项目
    async createProject(data: ApiProjectCreate) {
      try {
        const project = await projectApi.createProject(data)
        this.projects.unshift(project)
        this.total += 1
        return project
      } catch (error) {
        console.error('Failed to create project:', error)
        throw error
      }
    },

    // 更新项目
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
        console.error('Failed to update project:', error)
        throw error
      }
    },

    // 删除项目
    async deleteProject(id: number) {
      try {
        await projectApi.deleteProject(id)
        this.projects = this.projects.filter(p => p.id !== id)
        this.total -= 1
        if (this.currentProject?.id === id) {
          this.currentProject = null
        }
      } catch (error) {
        console.error('Failed to delete project:', error)
        throw error
      }
    },

    // 克隆项目
    async cloneProject(id: number, name: string) {
      try {
        const clonedProject = await projectApi.cloneProject(id, { name })
        this.projects.unshift(clonedProject)
        this.total += 1
        return clonedProject
      } catch (error) {
        console.error('Failed to clone project:', error)
        throw error
      }
    },

    // 清除当前项目
    clearCurrentProject() {
      this.currentProject = null
    }
  }
})