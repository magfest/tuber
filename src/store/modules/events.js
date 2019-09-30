import Vue from 'vue';

const state = {
  events: [],
  event: {},
};

// getters
const getters = {
  events: state => state.events,
  event: state => state.event,
};

// actions
const actions = {
  get_events({ commit, state }) {
    return new Promise((resolve, reject) => {
      fetch('/api/events/list').then((response) => {
        response.json().then((data) => {
          commit('set_events', data.events);
          commit('set_event', state.events[0]);
          resolve();
        });
      }).catch(() => {
        reject();
      });
    });
  },
};

// mutations
const mutations = {
  set_events(state, events) {
    Vue.set(state, 'events', events);
  },
  set_event(state, event) {
    state.event = event;
  },
};

export default {
  state,
  getters,
  actions,
  mutations,
};
