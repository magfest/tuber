import '@babel/polyfill'
import 'mutationobserver-shim'
import Vue from 'vue'
import './plugins/bootstrap-vue'
import App from './App.vue'
import './registerServiceWorker'
import router from './router'
import store from './store'

Vue.config.productionTip = false

import cookies from 'vue-cookies';
Vue.use(cookies);

import axios from 'axios';
axios.defaults.headers.common['Accept'] = 'application/json';
axios.defaults.headers.common['Content-Type'] = 'application/json';
axios.defaults.baseURL = '/api/';
const csrf_request = (request) => {
  console.log(request)
  if (request.method === 'get'){
    request.params = {
      csrf_token: cookies.get('csrf_token')
    }
  } else if (request.method === 'post'){
    request.data.csrf_token = cookies.get('csrf_token')
  }
  return request;
}

axios.interceptors.request.use(
  request => csrf_request(request)
)

import Notifications from 'vue-notification';
Vue.use(Notifications);


new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
