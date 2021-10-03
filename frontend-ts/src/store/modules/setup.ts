interface Setup {
  initialSetup: boolean
}

const state = () => ({
  initialSetup: true
})

// getters
const getters = {}

// actions
const actions = {
  async getInitialSetup ({ commit }) {
    const products = await shop.getProducts()
    commit('setProducts', products)
  }
}

// mutations
const mutations = {
  setProducts (state, products) {
    state.all = products
  },

  decrementProductInventory (state, { id }) {
    const product = state.all.find(product => product.id === id)
    product.inventory--
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
