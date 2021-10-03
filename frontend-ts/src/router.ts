import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from './components/Dashboard.vue'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: Dashboard
  }
]

export default createRouter({
  history: createWebHashHistory(),
  routes
})
