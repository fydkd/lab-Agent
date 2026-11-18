import { createRouter, createWebHistory } from 'vue-router'
import { getToken, getUserInfo } from "@/utils/auth.js";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/manager/home' },
    {
      path: '/manager',
      name: 'Layout',
      component: () => import('@/layouts/Layout.vue'),
      children: [
        { path: 'home', name: 'Home', component: () => import('@/views/Home.vue') },
        { path: 'lab', name: 'Lab', component: () => import('@/views/Lab.vue'), meta: { roles: ['admin'] } },
        { path: 'profile', name: 'Profile', component: () => import('@/views/Profile.vue') },
        { path: 'password', name: 'Password', component: () => import('@/views/Password.vue') },
        { path: 'user', name: 'User', component: () => import('@/views/User.vue'), meta: { roles: ['admin'] } },
        { path: 'equipment', name: 'Equipment', component: () => import('@/views/Equipment.vue'), meta: { roles: ['admin'] } },
        { path: 'lablist', name: 'LabList', component: () => import('@/views/LabList.vue') },
        { path: 'lab-equipment', name: 'LabEquipment', component: () => import('@/views/LabEquipment.vue') },
        { path: 'my-reservation', name: 'MyReservation', component: () => import('@/views/MyReservation.vue') },
        { path: 'audit-reservation', name: 'AuditReservation', component: () => import('@/views/AuditReservation.vue'), meta: { roles: ['admin'] } },
        { path: 'ai-chat', name: 'AIChat', component: () => import('@/views/AIChat.vue') },
      ]
    },
    { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
    { path: '/register', name: 'Register', component: () => import('@/views/Register.vue') }
  ]
})

router.beforeEach((to, from) => {
  const token = getToken()
  if (to.path === '/login' || to.path === '/register') {
    return true
  }
  if (!token) {
    return '/login'
  }
  // 角色权限校验：路由 meta.roles 声明允许的角色
  const allowedRoles = to.meta?.roles
  if (allowedRoles && allowedRoles.length > 0) {
    const userInfo = getUserInfo()
    const role = userInfo?.role
    if (!role || !allowedRoles.includes(role)) {
      // 无权限时跳回首页，避免进入管理员页面看到 403 错误
      return '/manager/home'
    }
  }
  return true
})

export default router
