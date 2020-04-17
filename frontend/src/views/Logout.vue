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
          self.notify('Failed to check whether you are logged in.');
        });
        self.notify('Logged out successfully!');
      } else {
        self.notify('Failed to log out. Were you logged in?');
      }
    }).catch(() => {
      self.notify('Network error while logging out.');
    });
  },
};
</script>
