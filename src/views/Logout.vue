<template>
  <div>
    <h1>You have logged out</h1>
  </div>
</template>

<style>
</style>

<script>
export default {
  name: 'Logout',
  data: () => ({
  }),
  mounted() {
    const self = this;
    this.post('/api/logout').then((resp) => {
      if (resp.success) {
        self.$store.dispatch('check_logged_in').then(() => {
          self.$router.push({ name: 'home' });
        }).catch(() => {
          self.$store.commit('open_snackbar', 'Failed to check whether you are logged in.');
        });
        self.$store.commit('open_snackbar', 'Logged out successfully!');
      } else {
        self.$store.commit('open_snackbar', 'Failed to log out. Were you logged in?');
      }
    }).catch(() => {
      self.$store.commit('open_snackbar', 'Network error while logging out.');
    });
  },
};
</script>
