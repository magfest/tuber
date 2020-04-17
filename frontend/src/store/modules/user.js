import Vue from 'vue';
import { get } from '../../mixins/rest';

const state = {
  initial_setup: false,
  user: {},
  logged_in: false,
  session: '',
  perms: [],
};

// getters
const getters = {
  initial_setup: state => state.initial_setup,
  user: state => state.user,
  logged_in: state => state.logged_in,
  perms: state => state.perms,
};

// actions
const actions = {
  check_initial_setup({ commit }) {
    return new Promise((resolve) => {
      get('/api/check_initial_setup').then((response) => {
        commit('update_initial_setup', response.initial_setup);
        resolve();
      }).catch(() => {
        commit('open_snackbar', 'Failed to check if server is in initial setup mode.');
      });
    });
  },
  check_logged_in({ commit }) {
    return new Promise((resolve) => {
      get('/api/check_login').then((response) => {
        if (response.success) {
          get('/api/user/permissions').then((perms) => {
            commit('set_perms', perms.permissions);
            commit('login', response);
            resolve();
          }).catch(() => {
            commit('open_snackbar', 'Failed to retrieve user permissions.');
          });
        } else {
          commit('logout');
          resolve();
        }
      }).catch(() => {
        commit('open_snackbar', 'Failed to check if logged in.');
      });
    });
  },
};

// mutations
const mutations = {
  update_initial_setup(state, value) {
    state.initial_setup = value;
  },
  login(state, data) {
    if (data.success) {
      Vue.set(state, 'logged_in', true);
      Vue.set(state, 'user', data.user);
      Vue.set(state, 'session', data.session);
    } else {
      Vue.set(state, 'logged_in', false);
    }
  },
  logout(state) {
    state.user = {};
    state.session = '';
    state.logged_in = false;
    Vue.set(state, 'perms', []);
  },
  set_perms(state, data) {
    Vue.set(state, 'perms', data);
  },
};

export default {
  state,
  getters,
  actions,
  mutations,
};
