import Vue from 'vue';
import cookies from 'vue-cookies';
import AsyncComputed from 'vue-async-computed';
import VueApexCharts from 'vue-apexcharts';
import App from './App.vue';
import router from './router';
import store from './store/store';
import vuetify from './vuetify';

import './mixins/index';

Vue.use(AsyncComputed);
Vue.use(cookies);
Vue.component('apexchart', VueApexCharts);

Vue.config.productionTip = false;

window.vue = new Vue({
  router,
  store,
  vuetify,
  render: h => h(App),
}).$mount('#app');
