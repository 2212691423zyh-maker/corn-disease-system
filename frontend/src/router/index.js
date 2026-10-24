import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/recognition' },
  { path: '/recognition', name: 'Recognition', component: () => import('@/views/Recognition.vue') },
  { path: '/chat', name: 'Chat', component: () => import('@/views/Chat.vue') },
  { path: '/knowledge', name: 'Knowledge', component: () => import('@/views/Knowledge.vue') },
  { path: '/plan', name: 'Plan', component: () => import('@/views/Plan.vue') },
  { path: '/dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
]

export default createRouter({ history: createWebHistory(), routes })
