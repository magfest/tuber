import Vue from 'vue';
import Vuex from 'vuex';
import events from './modules/events';
import user from './modules/user';
import snackbar from './modules/snackbar';

Vue.use(Vuex);

export default new Vuex.Store({
  modules: {
    events,
    user,
    snackbar,
  },
});
