<template>
  <v-app>
    <v-navigation-drawer v-model="drawer" app clipped>
      <v-list dense>
        <v-list-item>
          <v-list-item-action>
            <v-icon>mdi-view-dashboard</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title>Dashboard</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item>
          <v-list-item-action>
            <v-icon>mdi-settings</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title>Settings</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar app clipped-left>
      <v-app-bar-nav-icon @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title class="headline">
        <span>Tuber</span>
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <div>
        <v-select class="event-select" :items="events" item-text="name" item-value="id" :value="event.id" label="Event" outlined></v-select>
      </div>
    </v-app-bar>

    <v-content>
      <router-view/>
    </v-content>
    <v-snackbar v-if="snackbar">
      {{ snackbar_text }}
      <v-btn color="pink" :timeout="0" text @click="$store.commit('close_snackbar')">Close</v-btn>
    </v-snackbar>
  </v-app>
</template>

<style>
.event-select {
  padding-top: 30px !important;
}
</style>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'App',
  data: () => ({
    drawer: null,
  }),
  computed: {
    ...mapGetters([
      'snackbar',
      'snackbar_text',
      'initial_setup',
      'logged_in',
      'events',
      'event',
    ]),
  },
  mounted() {
    this.$vuetify.theme.dark = true;
    const self = this;
    this.$store.dispatch('check_logged_in').then(() => {
      self.$store.dispatch('check_initial_setup').then(() => {
        if (self.initial_setup) {
          if (self.$router.currentRoute.name !== 'home') {
            self.$router.push({ name: 'home' });
          }
        } else if (!self.logged_in) {
          if (self.$router.currentRoute.name !== 'login') {
            self.$router.push({ name: 'login' });
          }
        }
      });
    });
  },
  methods: {
    update() {
      this.$store.dispatch('get_events');
    },
  },
  watchers: {
    logged_in: () => {
      this.update();
    },
  },
};
</script>
