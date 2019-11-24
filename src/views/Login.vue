<template>
  <div>
    <div>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="login_loading">
        <v-card-title>Welcome to Tuber!</v-card-title>
        <v-card-text>
          <v-form>
            <p>Please log in:</p>
            <v-text-field label="Username" v-model="username" outlined></v-text-field>
            <v-text-field label="Password" v-model="password" type="password" outlined></v-text-field>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn outlined type="submit" @click.prevent="login">Login</v-btn>
            </v-card-actions>
          </v-form>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<style>
</style>

<script>
export default {
  name: 'Login',
  data: () => ({
    login_loading: false,
    username: '',
    password: '',
  }),
  methods: {
    login() {
      this.login_loading = true;
      const self = this;
      this.post('/api/login', {
        username: this.username,
        password: this.password,
      }).then((resp) => {
        if (resp.success) {
          self.$store.dispatch('check_logged_in').then(() => {
            self.$router.push({ name: 'home' });
          }).catch(() => {
            self.notify('Failed to check if you are logged in.');
          });
          self.notify('Logged in successfully!');
        } else {
          this.login_loading = false;
          self.notify('Failed to log in. Are your credentials correct?');
        }
      }).catch(() => {
        self.login_loading = false;
        self.notify('Network error while logging in.');
      });
    },
  },
};
</script>
