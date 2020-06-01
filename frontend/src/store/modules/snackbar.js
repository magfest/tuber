const state = {
  snackbar: false,
  snackbar_text: '',
};

// getters
const getters = {
  snackbar: (state) => state.snackbar,
  snackbar_text: (state) => state.snackbar_text,
};

// actions
const actions = {

};

// mutations
const mutations = {
  open_snackbar(state, text) {
    state.snackbar_text = text;
    state.snackbar = true;
  },
  close_snackbar(state) {
    state.snackbar = false;
  },
};

export default {
  state,
  getters,
  actions,
  mutations,
};
