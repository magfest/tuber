import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './components/Dashboard.vue'
import RoomRequest from './views/rooming/Request.vue'
import RoomApproval from './views/rooming/Approval.vue'
import RoomApprovals from './views/rooming/Approvals.vue'
import RoomSettings from './views/rooming/Settings.vue'
import RoomBlocks from './views/rooming/Blocks.vue'
import RoomAssignments from './views/rooming/Assignments.vue'
import UberLogin from './views/rooming/UberLogin.vue'
import UberDepartmentLogin from './views/rooming/UberDepartmentLogin.vue'

import { RoomTable, RequestTable } from './components/rooming'
import EmailSettings from './views/event/EmailSettings.vue'

import UserSettings from './views/settings/Users.vue'
import UserProfile from './views/settings/Profile.vue'
import Events from './views/settings/Events.vue'
import Badges from './views/event/Badges.vue'
import EventSettings from './views/event/Settings.vue'

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
    path: '/rooming/request',
    name: 'roomrequest',
    component: RoomRequest
  },
  {
    path: '/rooming/rooms',
    name: 'roomlist',
    component: RoomTable
  },
  {
    path: '/hotels/request',
    name: 'uberlogin',
    component: UberLogin
  },
  {
    path: '/rooming/approvals/:departmentID',
    name: 'roomapproval',
    component: RoomApproval,
    props: true
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
    path: '/rooming/settings',
    name: 'roomsettings',
    component: RoomSettings
  },
  {
    path: '/rooming/blocks',
    name: 'roomblocks',
    component: RoomBlocks
  },
  {
    path: '/rooming/requests',
    name: 'roomrequests',
    component: RequestTable
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
