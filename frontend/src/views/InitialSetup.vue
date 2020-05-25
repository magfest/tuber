<template>
  <div>
    <br>
    <v-card max-width="1000" :raised="true" class="mx-auto" :loading="initial_setup_loading">
      <v-card-title>Welcome to Tuber!</v-card-title>
      <v-card-text>
        <v-form>
          <p>Please create an admin account:</p>
          <v-text-field label="Username" v-model="username" outlined></v-text-field>
          <v-text-field label="Password" v-model="password" type="password" outlined></v-text-field>
          <v-text-field label="Email" v-model="email" outlined></v-text-field>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn outlined type="submit" @click.prevent="create_admin">Submit</v-btn>
          </v-card-actions>
        </v-form>
      </v-card-text>
    </v-card>
  </div>
</template>

<style>
</style>

<script>
export default {
  name: 'InitialSetup',
  data: () => ({
    initial_setup_loading: false,
    username: '',
    password: '',
    email: '',
  }),
  methods: {
    create_admin() {
      this.initial_setup_loading = true;
      const self = this;
      this.post('/api/initial_setup', {
        username: this.username,
        password: this.password,
        email: this.email,
      }).then(() => {
        self.$store.dispatch('check_initial_setup').then(() => {
          self.$router.push({ name: 'eventslist' });
        }).catch(() => {
          self.notify('Failed to check if server is in initial setup mode.');
        });
        self.notify('Created admin account successfully!');
      }).catch(() => {
        self.initial_setup_loading = false;
        self.notify('Failed to run initial setup.');
      });
    },
  },
};
</script>
