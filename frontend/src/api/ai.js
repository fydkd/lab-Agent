import request from "@/utils/request"
import { getToken } from "@/utils/auth"

/**
 * AI对话请求（非流式，已弃用，保留以备扩展）
 */
export function chatAPI(data) {
    return request({
        url: "/api/ai/chat",
        method: "post",
        data,
        timeout: 90000
    })
}

/**
 * AI 流式对话请求
 * @param {object} data - { messages: [...] }
 * @param {function} onEvent - 接收 SSE 事件的回调
 */
export async function streamChatAPI(data, onEvent) {
    const baseURL = import.meta.env.VITE_API_BASE_URL
    const token = getToken()
    // 流式接口整体超时（Agent 调用多轮工具，给足 120s）
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 120000)
    try {
        const res = await fetch(`${baseURL}/api/ai/chat/stream`, {
            method: "post",
            headers: {
                'Content-Type': 'application/json',
                Accept: 'text/event-stream',
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify(data),
            signal: controller.signal
        })
        if (res.status === 401) {
            throw new Error("token过期，请重新登录")
        }
        if (!res.ok || !res.body) {
            throw new Error("流式接口请求失败")
        }
        const contentType = res.headers.get('content-type') || ''
        if (!contentType.includes('text/event-stream')) {
            throw new Error("流式接口返回的不是事件流格式")
        }
        const reader = res.body.getReader()
        const decoder = new TextDecoder('utf-8')
        let buffer = ''

        while (true) {
            const { done, value } = await reader.read()
            if (done) break
            buffer += decoder.decode(value, { stream: true })

            const chunks = buffer.split('\n\n')
            buffer = chunks.pop()
            for (const chunk of chunks) {
                const line = chunk
                    .split('\n')
                    .map((item) => item.trim())
                    .find((item) => item.startsWith('data:'))
                if (!line) continue
                const payload = line.slice(5).trim()
                if (!payload || payload === '[DONE]') continue
                try {
                    onEvent(JSON.parse(payload))
                } catch {
                    // 忽略单条解析失败，不中断流
                }
            }
        }
    } finally {
        clearTimeout(timer)
    }
}
