import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login';
import Users from '../views/GlobalSettings/Users';
import Import from '../views/GlobalSettings/Import';
import MockData from '../components/Settings/MockData';
import Events from '../views/GlobalSettings/Events';

//------------ Global settings ----------------


Vue.use(VueRouter)

  const routes = [
    {
      path: '/',
      name: 'Home',
      component: Home
    },
    {
      path: '/about',
      name: 'About',
      // route level code-splitting
      // this generates a separate chunk (about.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import(/* webpackChunkName: "about" */ '../views/About.vue')
    },
    {
      path: '/users',
      name: 'GlobalSettings-Users',
      component: Users,
    },
    {
      path: '/events',
      name: 'GlobalSettings-Events',
      component: Events,
    },
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/import',
      name: 'Import',
      component: Import,
      children: [
        {
          path: 'mock',
          name: 'MockData',
          component: MockData,
        }
      ]
    }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
