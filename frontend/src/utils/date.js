/**
 * 全局时间格式化函数
 * 用法: formatDate(value) => 'YYYY-MM-DD HH:mm:ss'
 *      formatDate(value, 'YYYY-MM-DD')
 */
export function formatDate(value, fmt = 'YYYY-MM-DD HH:mm:ss') {
  if (!value) return '-'
  let d
  if (value instanceof Date) d = value
  else {
    // 兼容后端 ISO/带T 字符串、不带时区
    const v = typeof value === 'string' ? value.replace('T', ' ').replace(/\.\d+/, '').replace('Z', '') : value
    d = new Date(v)
  }
  if (isNaN(d.getTime())) return value || '-'

  const o = {
    YYYY: d.getFullYear(),
    MM: String(d.getMonth() + 1).padStart(2, '0'),
    DD: String(d.getDate()).padStart(2, '0'),
    HH: String(d.getHours()).padStart(2, '0'),
    mm: String(d.getMinutes()).padStart(2, '0'),
    ss: String(d.getSeconds()).padStart(2, '0')
  }
  return fmt.replace(/YYYY|MM|DD|HH|mm|ss/g, m => o[m])
}
