import Vue from 'vue';
import axios from 'axios';

export default {
  namespaced: true,
  state: {
    events: [],
    event: {}
  },

  mutations: {
    importEvents(state, events){
      Vue.set(state, 'events', events)
    },

    setEvent(state, event){
      let eObj = state.events.filter((e) => {return e.name === event})[0]
      Vue.set(state, 'event', eObj);
    }
  },

  actions: {
    getEvents({commit}){
      axios.get('events?full=true')
        .then(response => {
          commit('importEvents', response.data)
        })
    }
  }
}
