<template>
  <div>
    <div v-if="initial_setup">
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="initial_setup_loading">
        <v-card-title>Welcome to 2ber!</v-card-title>
        <v-card-text>
          <v-form>
            <p>Please create an admin account:</p>
            <v-text-field label="Username" v-model="username" outlined></v-text-field>
            <v-text-field label="Password" v-model="password" type="password" outlined></v-text-field>
            <v-text-field label="Email" v-model="email" outlined></v-text-field>
          </v-form>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn outlined @click="create_admin">Submit</v-btn>
          </v-card-actions>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'Home',
  data() {
    return {
      initial_setup_loading: false,
      username: '',
      password: '',
      email: '',
    };
  },
  computed: {
    ...mapGetters([
      'initial_setup',
    ]),
  },
  mounted() {
    this.$store.dispatch('check_initial_setup');
  },
  methods: {
    create_admin() {
      this.initial_setup_loading = true;
      const self = this;
      this.post('/api/initial_setup', {
        username: this.username,
        password: this.password,
        email: this.email,
      }).then((resp) => {
        if (resp.success) {
          self.$store.dispatch('check_initial_setup');
          self.$store.commit('open_snackbar', 'Created admin account successfully!');
        } else {
          self.$store.commit('open_snackbar', 'Failed to create admin account.');
        }
      }).catch(() => {
        self.initial_setup_loading = false;
        self.$store.commit('open_snackbar', 'Network error while creating admin account.');
      });
    },
  },
};
</script>
