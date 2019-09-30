import Vue from 'vue';
import Router from 'vue-router';
import Home from './views/Home.vue';
import Login from './views/Login.vue';
import StaffList from './views/StaffList.vue';
import StaffDetail from './views/StaffDetail.vue';
import DepartmentList from './views/DepartmentList.vue';
import DepartmentDetail from './views/DepartmentDetail.vue';

Vue.use(Router);

export default new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home,
    },
    {
      path: '/login',
      name: 'login',
      component: Login,
    },
    {
      path: '/staff',
      name: 'stafflist',
      component: StaffList,
    },
    {
      path: '/staff/:id',
      name: 'staffdetail',
      component: StaffDetail,
    },
    {
      path: '/departments',
      name: 'departmentlist',
      component: DepartmentList,
    },
    {
      path: '/departments/:id',
      name: 'departmentdetail',
      component: DepartmentDetail,
    },
  ],
});
