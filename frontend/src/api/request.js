/**
 * Axios封装
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: '/api',
  timeout: 60000
})

service.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = 'Bearer ' + token
  return config
})

service.interceptors.response.use(
  res => {
    const data = res.data
    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code === 200) return data
      if (data.code === 401) {
        ElMessage.error(data.msg || '登录已失效')
        localStorage.removeItem('token')
        window.location.href = '/login'
        return Promise.reject(data)
      }
      ElMessage.error(data.msg || '请求失败')
      return Promise.reject(data)
    }
    return data
  },
  err => {
    if (err.response && err.response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    ElMessage.error(err.message || '网络错误')
    return Promise.reject(err)
  }
)

export default service
