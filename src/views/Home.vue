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
    <div v-else-if="events.length == 0">
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="event_loading">
        <v-card-title>You don't have any events.</v-card-title>
        <v-card-text>
          <v-form>
            <p>Create your first event:</p>
            <v-text-field label="Name" v-model="name" outlined></v-text-field>
            <v-text-field label="Description" v-model="description" outlined></v-text-field>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn outlined @click="create_event">Submit</v-btn>
            </v-card-actions>
          </v-form>
        </v-card-text>
      </v-card>
    </div>
    <div v-else>
      <h1>{{ event.name }}</h1>
      <p>{{ event.description }}</p>
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
      event_loading: false,
      username: '',
      password: '',
      email: '',
      name: '',
      description: '',
    };
  },
  computed: {
    ...mapGetters([
      'initial_setup',
      'events',
      'event',
    ]),
  },
  mounted() {
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
          self.$store.dispatch('check_initial_setup').then(() => {
            self.$router.push('login');
          });
          self.$store.commit('open_snackbar', 'Created admin account successfully!');
        } else {
          self.$store.commit('open_snackbar', 'Failed to create admin account.');
        }
      }).catch(() => {
        self.initial_setup_loading = false;
        self.$store.commit('open_snackbar', 'Network error while creating admin account.');
      });
    },
    create_event() {
      this.event_loading = true;
      const self = this;
      this.post('/api/events/create', {
        name: this.name,
        description: this.description,
      }).then((resp) => {
        if (resp.success) {
          self.$store.dispatch('get_events').then(() => {
            self.$store.commit('set_event', resp.event.id);
          });
          self.$store.commit('open_snackbar', 'Created event successfully!');
        } else {
          self.$store.commit('open_snackbar', 'Failed to create event.');
        }
      }).catch(() => {

      });
    },
  },
};
</script>
