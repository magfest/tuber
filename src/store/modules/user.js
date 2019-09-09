const state = {
  initial_setup: false,
};

// getters
const getters = {
  initial_setup: state => state.initial_setup,
};

// actions
const actions = {
  check_initial_setup({ commit }) {
    fetch('/api/check_initial_setup').then((response) => {
      response.json().then((data) => {
        commit('update_initial_setup', data.initial_setup);
      });
    });
  },
};

// mutations
const mutations = {
  update_initial_setup(state, value) {
    state.initial_setup = value;
  },
};

export default {
  state,
  getters,
  actions,
  mutations,
};
