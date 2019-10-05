<template>
  <div>
  </div>
</template>

<style>
</style>

<script>
export default {
  name: '',
  data: () => ({
  }),
  mounted() {
    const self = this;
    this.post('/api/hotels/staffer_auth', {
      token: this.$route.query.id,
    }).then((resp) => {
      if (resp.success) {
        self.$store.dispatch('check_logged_in').then(() => {
          self.$store.commit('open_snackbar', 'It worked!');
        });
      } else {
        // TODO: Push the user back to Uber?
        // self.$store.commit('open_snackbar', 'Failed to log in. Are your credentials correct?');
      }
    }).catch(() => {
      self.$store.commit('open_snackbar', 'Network error while logging in.');
    });
  },
};
</script>
