import Vue from 'vue';

function notify(text) {
  this.$store.commit('open_snackbar', text);
}

Vue.mixin({ methods: { notify } });

export default { notify };
