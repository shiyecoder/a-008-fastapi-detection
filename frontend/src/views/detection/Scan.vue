<template>
  <div>
    <div class="app-card">
      <h3 style="margin:0 0 16px 0;">文件检测</h3>
      <el-form label-width="100px">
        <el-form-item label="检测类型">
          <el-radio-group v-model="form.detect_type">
            <el-radio value="static">静态检测</el-radio>
            <el-radio value="dynamic">动态行为分析</el-radio>
            <el-radio value="mixed">综合检测</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="选择文件">
          <el-upload
            ref="upRef"
            action="#"
            :auto-upload="false"
            :on-change="onChange"
            :on-remove="onRemove"
            :file-list="fileList"
            multiple
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div style="font-size:12px;color:#909399;margin-top:6px;">
                支持 PHP/JSP/ASP/Python/Java 等Web脚本文件，可多选
              </div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSubmit">开始检测</el-button>
          <el-button @click="onReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div v-if="results.length" class="app-card">
      <h3 style="margin:0 0 16px 0;">检测结果</h3>
      <el-table :data="results" stripe>
        <el-table-column prop="file_name" label="文件名" />
        <el-table-column prop="language" label="语言" />
        <el-table-column prop="file_size" label="大小(B)" />
        <el-table-column label="风险等级">
          <template #default="{ row }">
            <span :class="'tag-' + row.risk_level">{{ riskMap[row.risk_level] }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="风险分" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="detailVisible" title="检测详情" width="800px">
      <pre style="white-space:pre-wrap;background:#f5f7fa;padding:12px;border-radius:4px;font-size:12px;">{{ detailJson }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { detectionApi } from '@/api'

const form = reactive({ detect_type: 'mixed' })
const fileList = ref([])
const loading = ref(false)
const results = ref([])
const detailVisible = ref(false)
const detailJson = ref('')
const riskMap = { high: '高危', medium: '中危', low: '低危', safe: '安全' }

function onChange(file) {
  // el-upload 绑定了 :file-list 时为受控模式，需手动维护
  if (!fileList.value.find(f => f.uid === file.uid)) {
    fileList.value.push(file)
  }
}
function onRemove(file) {
  fileList.value = fileList.value.filter(f => f.uid !== file.uid)
}
function onReset() { fileList.value = []; results.value = [] }

async function onSubmit() {
  if (!fileList.value.length) { ElMessage.warning('请选择文件'); return }
  loading.value = true
  results.value = []
  try {
    for (const f of fileList.value) {
      const raw = f.raw || f
      const fd = new FormData()
      fd.append('file', raw)
      fd.append('detect_type', form.detect_type)
      fd.append('task_name', (raw && raw.name) || f.name || '未命名任务')
      try {
        const res = await detectionApi.scan(fd)
        results.value.push(res.data)
      } catch (e) { console.error(e) }
    }
    ElMessage.success(`检测完成，共 ${results.value.length} 个文件`)
  } finally { loading.value = false }
}

function showDetail(row) {
  detailJson.value = JSON.stringify(row, null, 2)
  detailVisible.value = true
}
</script>
