import Vue from 'vue';
import cookies from 'vue-cookies';
import App from './App.vue';
import router from './router';
import store from './store/store';
import vuetify from './vuetify';
import './mixins/index';

Vue.use(cookies);

Vue.config.productionTip = false;

window.vue = new Vue({
  router,
  store,
  vuetify,
  render: h => h(App),
}).$mount('#app');
