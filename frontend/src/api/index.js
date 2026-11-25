/**
 * API：聚合所有模块（按需取用）
 */
import req from './request'

export const authApi = {
  login: data => req.post('/auth/login', data),
  register: data => req.post('/auth/register', data),
  info: () => req.get('/auth/info'),
  logout: () => req.post('/auth/logout')
}

export const profileApi = {
  update: data => req.put('/profile/update', data),
  password: data => req.put('/profile/password', data),
  uploadAvatar: file => {
    const fd = new FormData()
    fd.append('file', file)
    return req.post('/profile/avatar', fd)
  }
}

export const userApi = {
  page: params => req.get('/user/page', { params }),
  add: data => req.post('/user/add', data),
  update: (id, data) => req.put(`/user/update/${id}`, data),
  del: id => req.delete(`/user/delete/${id}`),
  resetPwd: id => req.put(`/user/reset-password/${id}`)
}

export const roleApi = {
  page: params => req.get('/role/page', { params }),
  all: () => req.get('/role/all'),
  add: data => req.post('/role/add', data),
  update: (id, data) => req.put(`/role/update/${id}`, data),
  del: id => req.delete(`/role/delete/${id}`),
  getMenus: id => req.get(`/role/menu/${id}`),
  assignMenu: (id, menu_ids) => req.post(`/role/assign-menu/${id}`, { menu_ids })
}

export const menuApi = {
  tree: () => req.get('/menu/tree'),
  add: data => req.post('/menu/add', data),
  update: (id, data) => req.put(`/menu/update/${id}`, data),
  del: id => req.delete(`/menu/delete/${id}`)
}

export const dashboardApi = {
  overview: () => req.get('/dashboard/overview'),
  trend: () => req.get('/dashboard/trend'),
  langDist: () => req.get('/dashboard/lang-distribution'),
  detectType: () => req.get('/dashboard/detect-type'),
  riskLevel: () => req.get('/dashboard/risk-level'),
  alertStatus: () => req.get('/dashboard/alert-status'),
  recentAlerts: (limit = 8) => req.get('/dashboard/recent-alerts', { params: { limit } }),
  recentQuarantine: (limit = 8) => req.get('/dashboard/recent-quarantine', { params: { limit } }),
  myStats: () => req.get('/dashboard/my-stats'),
  myTrend: () => req.get('/dashboard/my-trend')
}

export const detectionApi = {
  scan: fd => req.post('/detection/scan', fd),
  page: params => req.get('/detection/page', { params }),
  detail: id => req.get(`/detection/detail/${id}`),
  scope: id => req.get(`/detection/scope/${id}`),
  del: id => req.delete(`/detection/delete/${id}`),
  quarantine: id => req.post(`/detection/quarantine/${id}`)
}

export const yaraApi = {
  page: params => req.get('/yara/page', { params }),
  add: data => req.post('/yara/add', data),
  update: (id, data) => req.put(`/yara/update/${id}`, data),
  del: id => req.delete(`/yara/delete/${id}`),
  toggle: id => req.put(`/yara/toggle/${id}`)
}

export const signatureApi = {
  page: params => req.get('/signature/page', { params }),
  add: data => req.post('/signature/add', data),
  update: (id, data) => req.put(`/signature/update/${id}`, data),
  del: id => req.delete(`/signature/delete/${id}`),
  toggle: id => req.put(`/signature/toggle/${id}`)
}

export const hashLibApi = {
  page: params => req.get('/hash-lib/page', { params }),
  add: data => req.post('/hash-lib/add', data),
  update: (id, data) => req.put(`/hash-lib/update/${id}`, data),
  del: id => req.delete(`/hash-lib/delete/${id}`),
  toggle: id => req.put(`/hash-lib/toggle/${id}`)
}

export const quarantineApi = {
  page: params => req.get('/quarantine/page', { params }),
  restore: id => req.put(`/quarantine/restore/${id}`),
  del: id => req.delete(`/quarantine/delete/${id}`)
}

export const alertApi = {
  page: params => req.get('/alert/page', { params }),
  handle: (id, data) => req.put(`/alert/handle/${id}`, data),
  del: id => req.delete(`/alert/delete/${id}`)
}

export const vulnFixApi = {
  page: params => req.get('/vuln-fix/page', { params }),
  add: data => req.post('/vuln-fix/add', data),
  update: (id, data) => req.put(`/vuln-fix/update/${id}`, data),
  del: id => req.delete(`/vuln-fix/delete/${id}`)
}

export const reportApi = {
  page: params => req.get('/report/page', { params }),
  generate: data => req.post('/report/generate', data),
  detail: id => req.get(`/report/detail/${id}`),
  del: id => req.delete(`/report/delete/${id}`)
}

export const logApi = {
  page: params => req.get('/log/page', { params }),
  del: id => req.delete(`/log/delete/${id}`),
  clear: () => req.delete('/log/clear')
}
