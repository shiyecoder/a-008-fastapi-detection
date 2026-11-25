/**
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userId: null,
    username: '',
    nickname: '',
    avatar: '',
    email: '',
    phone: '',
    roles: [],
    perms: [],
    menus: []
  }),
  actions: {
    setToken(t) {
      this.token = t
      localStorage.setItem('token', t)
    },
    async loadInfo() {
      const res = await authApi.info()
      const d = res.data
      this.userId = d.userId
      this.username = d.username
      this.nickname = d.nickname
      this.avatar = d.avatar
      this.email = d.email
      this.phone = d.phone
      this.roles = d.roles || []
      this.perms = d.perms || []
      this.menus = d.menus || []
      return d
    },
    setAvatar(a) { this.avatar = a },
    setProfile(p) {
      if (p.nickname !== undefined) this.nickname = p.nickname
      if (p.email !== undefined) this.email = p.email
      if (p.phone !== undefined) this.phone = p.phone
    },
    logout() {
      this.token = ''
      localStorage.removeItem('token')
      this.userId = null
      this.username = ''
      this.nickname = ''
      this.avatar = ''
      this.roles = []
      this.menus = []
    }
  }
})
