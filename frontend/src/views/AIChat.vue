<template>
    <div>
        <el-card>
            <template #header>
                <div style="font-size: 16px; font-weight: bold">
                    <span>AI智能助手</span>
                </div>
            </template>
            <div 
              ref="listRef"
              style="
                height:480px; 
                overflow-y: auto;
                padding: 8px 4px;
                background-color: #fafafa;
                border-radius: 6px;
              "
            >
                <div 
                  v-for="(item, index) in messages" 
                  :key="index" 
                  :style="{
                    display: 'flex', 
                    justifyContent: item.role === 'user' ? 'flex-end' : 'flex-start',
                    marginBottom: '12px'
                    }"
                >
                    <div 
                      :style="{ 
                        maxWidth: '70%', 
                        padding: '10px 12px', 
                        borderRadius: '8px', 
                        backgroundColor: item.role === 'user' ? '#4091ff' : '#fff',
                        color: item.role === 'user' ? '#fff' : '#333',
                        lineHeight: '1.6',
                        boxShadow: '0 1px 2px rgba(0, 0, 0, 0.06)'
                        }"
                        >
                        <div 
                            v-if="item.role === 'assistant' && item.status"
                            style="margin-bottom: 6px; font-size: 12px; color: #909399">
                                {{ item.status }}
                        </div>
                        <div 
                            v-if="item.role === 'assistant' && item.steps?.length"
                            style="margin-bottom: 8px; font-size: 12px; color: #909399; line-height: 1.5">
                                <div v-for="(step,i) in item.steps" :key="i">. {{ step }}</div>
                        </div>
                        <div v-html="parseMarkdown(item.content)"></div>
                    </div>
                </div>
            </div>
            <div style="margin-top: 12px; display: flex; gap: 8px; align-items: flex-end;">
                <el-input 
                  v-model="input"
                  type="textarea" 
                  :rows="2" 
                  placeholder="问问实验室怎么预约、开放时间..." 
                  @keydown.enter.exact.prevent="sendMessage"
                  @keydown.enter.shift.stop
                  />
                <el-button type="primary" @click="sendMessage" :loading="loading">发送</el-button>
            </div>
        </el-card>
    </div>
</template>

<script setup>
import { ref, reactive, nextTick } from "vue"
import { streamChatAPI } from "@/api/ai"
import { ElMessage } from "element-plus"
import { marked } from "marked"
import DOMPurify from "dompurify"

// marked 全局配置只需设置一次，避免每次渲染重复配置
marked.setOptions({ breaks: true })

const messages = ref([
    {
        role: 'assistant',
        content: '您好，我是实验室AI智能助手。您可以向我提问怎么预约、取消。也可以说 [帮我预约明天下午的化学实验室]，确认后我会帮你提交预约。'
    }
])

const input = ref('')
const loading = ref(false)
const listRef = ref()

const scrollToBottom = () => {
    nextTick(() => {
        const elem = listRef.value
        if (elem) {
            elem.scrollTop = elem.scrollHeight
        }
    })
}

const sendMessage = async () => {
    const text = input.value.trim()
    if (!text || loading.value) return

    messages.value.push({role: 'user', content: text})
    input.value = ''
    loading.value = true
    scrollToBottom()

    const assistant = reactive({
        role: 'assistant',
        content: '',
        status: '正在思考...',
        steps: []
    })
    messages.value.push(assistant)

    const history = messages.value
        .filter((item) => item.role === 'user' || item.role === 'assistant')
        .slice(0, -1)
        .map(({ role, content }) => ({ role, content }))

       try {
        await streamChatAPI({messages: history}, (evt) => {
            if (evt.type === 'status') {
                assistant.status = evt.message || '正在思考...'
            } else if (evt.type === 'tool_start') {
                const label = evt.label || evt.name || '工具'
                assistant.status = `正在 ${label}...`
                assistant.steps.push(`开始：${label}`)
            } else if (evt.type === 'tool_end') {
                const label = evt.label || evt.name || '工具'
                assistant.status = `已完成：${label}`
                assistant.steps.push(`完成：${label}`)
                if (evt.preview) {
                    assistant.steps.push(`输出结果：${evt.preview}`)
                }
            } else if (evt.type === 'token') {
                assistant.content += evt.content || ''
                assistant.status = ''
            } else if (evt.type === 'done') {
                assistant.status = ''
            } else if (evt.type === 'error') {
                assistant.status = ''
                if (!assistant.content) {
                    assistant.content = evt.message || '请求失败'
                }
                ElMessage.error(evt.message || '请求失败')
            }
            scrollToBottom()
        })
    } catch (err) {
        assistant.status = ''
        if (!assistant.content) {
            assistant.content = err.message || '网络错误'
        }
        ElMessage.error(err.message || '网络错误')
    } finally {
        loading.value = false
        assistant.status = ''
        scrollToBottom()
    }
}

const parseMarkdown = (text) => {
    if (!text) return ''
    const rawHTML = marked.parse(text)
    return DOMPurify.sanitize(rawHTML)
}
</script>
