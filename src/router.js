import Vue from 'vue';
import Router from 'vue-router';
import Home from './views/Home.vue';
import Login from './views/Login.vue';
import Logout from './views/Logout.vue';
import StaffList from './views/StaffList.vue';
import StaffDetail from './views/StaffDetail.vue';
import DepartmentList from './views/DepartmentList.vue';
import DepartmentDetail from './views/DepartmentDetail.vue';
import HotelRequest from './views/Hotels/Request.vue';
import EventCreate from './views/Events/Create.vue';
import InitialSetup from './views/InitialSetup.vue';
import ImportStaff from './views/Importer/Staff.vue';
import store from './store/store';

Vue.use(Router);

const router = new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home,
    },
    {
      path: '/initialsetup',
      name: 'initialsetup',
      component: InitialSetup,
    },
    {
      path: '/login',
      name: 'login',
      component: Login,
    },
    {
      path: '/logout',
      name: 'logout',
      component: Logout,
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
    {
      path: '/hotels/request',
      name: 'hotelsrequest',
      component: HotelRequest,
    },
    {
      path: '/events/create',
      name: 'eventcreate',
      component: EventCreate,
    },
    {
      path: '/import/staff',
      name: 'importstaff',
      component: ImportStaff,
    },
  ],
});

function json(response) {
  return response.json();
}

function post(url, data) {
  data.csrf_token = window.$cookies.get('csrf_token');
  const promise = new Promise(((resolve, reject) => {
    fetch(url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    }).then(json).then((data) => {
      resolve(data);
    }).catch((error) => {
      reject(error);
    });
  }));
  return promise;
}

router.beforeEach((to, from, next) => {
  if (to.name === 'hotelsrequest') {
    if (Object.prototype.hasOwnProperty.call(to.query, 'id')) {
      post('/api/hotels/staffer_auth', {
        token: to.query.id,
      }).then((resp) => {
        if (resp.success) {
          store.dispatch('check_logged_in').then(() => {
            store.dispatch('get_events').then(() => {
              next();
            });
          });
        }
      });
    } else {
      next({ name: 'login' });
    }
  } else {
    store.dispatch('check_logged_in').then(() => {
      if (store.getters.logged_in) {
        store.dispatch('get_events').then(() => {
          if (store.getters.events.length === 0 && to.name !== 'eventcreate') {
            next({ name: 'eventcreate' });
          }
          next();
        }).catch(() => {
          next();
        });
      } else {
        store.dispatch('check_initial_setup').then(() => {
          if (store.getters.initial_setup) {
            if (to.name !== 'initialsetup') {
              next({ name: 'initialsetup' });
            }
          } else if (to.name !== 'login') {
            next({ name: 'login' });
          }
          next();
        }).catch(() => {
          next();
        });
      }
    });
  }
});

export default router;
