import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocation } from 'vue-router'
import Dashboard from './components/Dashboard.vue'
import RoomRequest from './views/rooming/Request.vue'
import RoomApprovals from './views/rooming/Approvals.vue'
import RoomSettings from './views/rooming/Settings.vue'
import RoomAssignments from './views/rooming/Assignments.vue'
import RoomingDashboard from './views/rooming/RoomingDashboard.vue'
import RoomRequests from './views/rooming/Requests.vue'
import UberLogin from './views/rooming/UberLogin.vue'
import UberDepartmentLogin from './views/rooming/UberDepartmentLogin.vue'

import EmailSettings from './views/event/EmailSettings.vue'

import UserSettings from './views/settings/Users.vue'
import UserProfile from './views/settings/Profile.vue'
import Events from './views/settings/Events.vue'
import Badges from './views/event/Badges.vue'
import EventSettings from './views/event/Settings.vue'

import Actions from './views/Actions.vue'
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
    path: '/rooming',
    name: 'roomingdashboard',
    component: RoomingDashboard
  },
  {
    path: '/rooming/request',
    name: 'roomrequest',
    component: RoomRequest
  },
  {
    path: '/hotels/request',
    name: 'uberlogin',
    component: UberLogin
  },
  {
    path: '/rooming/approvals/:departmentID',
    redirect: (to: RouteLocation) => ({
      path: '/rooming/approvals',
      query: { department: to.params.departmentID }
    })
  },
  {
    path: '/rooming/approvals',
    name: 'roomapprovals',
    component: RoomApprovals
  },
  {
    path: '/rooming/assignments',
    name: 'roomassignments',
    component: RoomAssignments
  },
  {
    path: '/rooming/rooms',
    redirect: '/rooming/assignments'
  },
  {
    path: '/rooming/missing_shifts',
    redirect: { path: '/rooming/requests', query: { afilter: 'missing_shifts' } }
  },
  {
    path: '/rooming/blocks',
    redirect: '/rooming/requests'
  },
  {
    path: '/rooming/settings',
    name: 'roomsettings',
    component: RoomSettings
  },
  {
    path: '/rooming/requests',
    name: 'roomrequests',
    component: RoomRequests
  },
  {
    path: '/hotels/approvals',
    name: 'uberdepartmentlogin',
    component: UberDepartmentLogin
  },
  {
    path: '/email',
    name: 'emailsettings',
    component: EmailSettings
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
    path: '/settings/events',
    name: 'events',
    component: Events
  },
  {
    path: '/user/profile',
    name: 'userprofile',
    component: UserProfile
  },
  {
    path: '/settings',
    name: 'eventsettings',
    component: EventSettings
  },
  {
    path: '/actions',
    name: 'actions',
    component: Actions
  },
  {
    path: '/settings/users',
    name: 'usersettings',
    component: UserSettings
  },
  {
    path: '/badges',
    name: 'badges',
    component: Badges
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
  history: createWebHistory(),
  routes
})
