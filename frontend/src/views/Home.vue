<template>
  <div>
    <!-- 欢迎横幅 -->
    <el-card style="background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%); border: none;">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <div style="font-size: 22px; font-weight: bold; color: #fff;">
            {{ greeting }}，{{ userInfo?.name }}
          </div>
          <div style="margin-top: 8px; font-size: 14px; color: rgba(255,255,255,0.85);">
            欢迎使用智能实验室预约系统，今天是 {{ today }}
          </div>
        </div>
        <el-tag effect="dark" style="background: rgba(255,255,255,0.2); border: none; color: #fff;">
          {{ userInfo?.role === 'admin' ? '管理员' : '学生' }}
        </el-tag>
      </div>
    </el-card>

    <!-- 数据统计 -->
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col v-for="item in statCards" :key="item.label" :span="6">
        <el-card shadow="hover">
          <div style="display: flex; align-items: center;">
            <div :style="{ width: '48px', height: '48px', borderRadius: '8px', backgroundColor: item.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }">
              <el-icon :size="24" :color="item.color"><component :is="item.icon" /></el-icon>
            </div>
            <div style="margin-left: 12px;">
              <div style="font-size: 13px; color: #909399;">{{ item.label }}</div>
              <div style="font-size: 24px; font-weight: bold; margin-top: 4px;" v-loading="statLoading">{{ item.value }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px;">
      <!-- 快捷入口 -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <div style="font-size: 16px; font-weight: bold;">快捷入口</div>
          </template>
          <div style="display: flex; flex-wrap: wrap; gap: 12px;">
            <div
              v-for="entry in quickEntries"
              :key="entry.path"
              @click="router.push(entry.path)"
              style="flex: 1 1 40%; min-width: 140px; display: flex; align-items: center; padding: 14px; border: 1px solid #ebeef5; border-radius: 8px; cursor: pointer; transition: all 0.2s;"
              @mouseenter="$event.currentTarget.style.borderColor = '#409eff'"
              @mouseleave="$event.currentTarget.style.borderColor = '#ebeef5'"
            >
              <el-icon :size="22" :color="entry.color"><component :is="entry.icon" /></el-icon>
              <span style="margin-left: 8px; font-size: 14px;">{{ entry.label }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 最新预约 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 16px; font-weight: bold;">最新预约</span>
              <el-button text type="primary" @click="router.push(userInfo?.role === 'admin' ? '/manager/audit-reservation' : '/manager/my-reservation')">查看更多</el-button>
            </div>
          </template>
          <el-table :data="recentReservations" v-loading="recentLoading" size="small">
            <el-table-column prop="lab_name" label="实验室" min-width="110" />
            <el-table-column prop="date" label="日期" width="110" />
            <el-table-column label="时段" width="140">
              <template #default="{ row }">
                {{ row.start_time }} - {{ row.end_time }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="暂无预约记录" :image-size="60" />
            </template>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUser } from '@/utils/user'
import { getLabPageList } from '@/api/lab'
import { getUserPageList } from '@/api/user'
import { getReservationPageList } from '@/api/reservation'
import router from '@/router'
import {
  OfficeBuilding, Tickets, ChatDotRound, House, Setting,
  DocumentChecked, User, Clock, CircleCheck
} from '@element-plus/icons-vue'
import { getReservationStatusText, getReservationStatusTagType } from '@/utils/constants'

const { userInfo } = useUser()
const isAdmin = computed(() => userInfo.value?.role === 'admin')

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const today = new Date().toLocaleDateString('zh-CN', {
  year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
})

// 数据统计
const stats = ref({ lab: 0, reservation: 0, pending: 0, approved: 0, user: 0 })
const statLoading = ref(false)

const statCards = computed(() => {
  if (isAdmin.value) {
    return [
      { label: '实验室总数', value: stats.value.lab, icon: OfficeBuilding, color: '#409eff', bg: '#ecf5ff' },
      { label: '预约总数', value: stats.value.reservation, icon: Tickets, color: '#67c23a', bg: '#f0f9eb' },
      { label: '待审核预约', value: stats.value.pending, icon: Clock, color: '#e6a23c', bg: '#fdf6ec' },
      { label: '用户总数', value: stats.value.user, icon: User, color: '#f56c6c', bg: '#fef0f0' },
    ]
  }
  return [
    { label: '实验室总数', value: stats.value.lab, icon: OfficeBuilding, color: '#409eff', bg: '#ecf5ff' },
    { label: '我的预约', value: stats.value.reservation, icon: Tickets, color: '#67c23a', bg: '#f0f9eb' },
    { label: '待审核', value: stats.value.pending, icon: Clock, color: '#e6a23c', bg: '#fdf6ec' },
    { label: '已通过', value: stats.value.approved, icon: CircleCheck, color: '#909399', bg: '#f4f4f5' },
  ]
})

// 快捷入口
const quickEntries = computed(() => {
  if (isAdmin.value) {
    return [
      { label: '实验室管理', path: '/manager/lab', icon: House, color: '#409eff' },
      { label: '设备管理', path: '/manager/equipment', icon: Setting, color: '#67c23a' },
      { label: '预约审核', path: '/manager/audit-reservation', icon: DocumentChecked, color: '#e6a23c' },
      { label: '用户管理', path: '/manager/user', icon: User, color: '#f56c6c' },
      { label: 'AI智能助手', path: '/manager/ai-chat', icon: ChatDotRound, color: '#909399' },
    ]
  }
  return [
    { label: '实验室列表', path: '/manager/lablist', icon: OfficeBuilding, color: '#409eff' },
    { label: '我的预约', path: '/manager/my-reservation', icon: Tickets, color: '#67c23a' },
    { label: 'AI智能助手', path: '/manager/ai-chat', icon: ChatDotRound, color: '#e6a23c' },
  ]
})

// 最新预约
const recentReservations = ref([])
const recentLoading = ref(false)

const statusType = (status) => getReservationStatusTagType(status)
const statusText = (status) => getReservationStatusText(status)

const countByStatus = async (status) => {
  const res = await getReservationPageList({ page: 1, page_size: 1, status })
  return res.code === 200 ? (res.data?.total || 0) : 0
}

const loadStats = async () => {
  statLoading.value = true
  try {
    const [labRes, total, pending] = await Promise.all([
      getLabPageList({ page: 1, page_size: 1 }),
      countByStatus(null),
      countByStatus(0),
    ])
    stats.value.lab = labRes.code === 200 ? (labRes.data?.total || 0) : 0
    stats.value.reservation = total
    stats.value.pending = pending

    if (isAdmin.value) {
      const userRes = await getUserPageList({ page: 1, page_size: 1 })
      stats.value.user = userRes.code === 200 ? (userRes.data?.total || 0) : 0
    } else {
      stats.value.approved = await countByStatus(1)
    }
  } finally {
    statLoading.value = false
  }
}

const loadRecent = async () => {
  recentLoading.value = true
  try {
    const res = await getReservationPageList({ page: 1, page_size: 5 })
    if (res.code === 200) {
      recentReservations.value = res.data?.list || []
    }
  } finally {
    recentLoading.value = false
  }
}

onMounted(() => {
  loadStats()
  loadRecent()
})
</script>
