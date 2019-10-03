import Vue from 'vue';

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
    return new Promise((resolve, reject) => {
      fetch('/api/check_initial_setup').then((response) => {
        response.json().then((data) => {
          commit('update_initial_setup', data.initial_setup);
          resolve();
        });
      }).catch(() => {
        reject();
      });
    });
  },
  check_logged_in({ commit }) {
    return new Promise((resolve, reject) => {
      fetch('/api/check_login').then((response) => {
        response.json().then((data) => {
          if (data.success) {
            fetch('/api/user/permissions').then((perms) => {
              perms.json().then((permdata) => {
                commit('set_perms', permdata.permissions);
                commit('login', data);
                resolve();
              });
            }).catch(() => {
              reject();
            });
          } else {
            commit('logout');
            resolve();
          }
        });
      }).catch(() => {
        reject();
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
