import Vue from 'vue'
import Vuex from 'vuex'

//------------MODULES-----------------
import events from './modules/events';

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
  },
  mutations: {
  },
  actions: {
  },
  modules: {
    events,
  }
})
