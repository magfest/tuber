import { createStore } from 'vuex'

// import setup from './modules/setup'

const debug = process.env.NODE_ENV !== 'production'

export default createStore({
  modules: {
    //    setup
  },
  strict: debug
})
