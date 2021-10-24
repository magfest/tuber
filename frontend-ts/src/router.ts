import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from './components/Dashboard.vue'
import RoomRequest from './views/rooming/Request.vue'

import Login from './views/Login.vue'
import Logout from './views/Logout.vue'

import InitialSetup from './views/setup/InitialSetup.vue'
import SetupWelcome from './views/setup/SetupWelcome.vue'
import SetupUser from './views/setup/SetupUser.vue'
import SetupEvent from './views/setup/SetupEvent.vue'
const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: Dashboard
  },
  {
    path: '/rooming/requests',
    name: 'roomrequest',
    component: RoomRequest
  },
  {
    path: '/login',
    name: 'login',
    component: Login
  },
  {
    path: '/logout',
    name: 'logout',
    component: Logout
  },
  {
    path: '/initialsetup',
    name: 'initialsetup',
    component: InitialSetup,
    children: [
      {
        path: 'welcome',
        name: 'welcome',
        component: SetupWelcome
      },
      {
        path: 'user',
        name: 'setupuser',
        component: SetupUser
      },
      {
        path: 'event',
        name: 'setupevent',
        component: SetupEvent
      }
    ]
  }
]

export default createRouter({
  history: createWebHashHistory(),
  routes
})
