<template>
  <div>
    <div>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="login_loading">
        <v-card-title>Welcome to 2ber!</v-card-title>
        <v-card-text>
          <v-form>
            <p>Please log in:</p>
            <v-text-field label="Username" v-model="username" outlined></v-text-field>
            <v-text-field label="Password" v-model="password" type="password" outlined></v-text-field>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn outlined type="submit" @click="login">Login</v-btn>
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
  name: '',
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
          });
          self.$store.commit('open_snackbar', 'Logged in successfully!');
        } else {
          this.login_loading = false;
          self.$store.commit('open_snackbar', 'Failed to log in. Are your credentials correct?');
        }
      }).catch(() => {
        self.login_loading = false;
        self.$store.commit('open_snackbar', 'Network error while logging in.');
      });
    },
  },
};
</script>
