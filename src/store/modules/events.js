import Vue from 'vue';
import { get } from '../../mixins/rest';

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
  get_events({ commit }) {
    return new Promise((resolve) => {
      get('/api/events', { full: true }).then((events) => {
        commit('set_events', events);
        resolve();
      }).catch(() => {
        commit('open_snackbar', 'Failed to retrieve list of events.');
      });
    });
  },
};

// mutations
const mutations = {
  set_events(state, events) {
    Vue.set(state, 'events', events);
    if (state.event) {
      for (let i = 0; i < state.events.length; i += 1) {
        if (state.events[i].id === state.event.id) {
          return;
        }
      }
      if (state.events.length > 0) {
        [state.event] = events;
      }
    }
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
