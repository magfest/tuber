<template>
  <v-app>
    <v-navigation-drawer v-model="drawer" app :clipped="true">
      <v-list dense nav>
        <v-list-item v-if="show_hotel" link>
          <v-list-item-icon>
            <v-icon>hotel</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Hotels</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item v-if="show_event_settings" link>
          <v-list-item-icon>
            <v-icon>settings</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Event Settings</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item v-if="logged_in" link>
          <v-list-item-icon>
            <v-icon>lock</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Logout</v-list-item-title>
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
        <v-select class="event-select" :items="events" item-text="name" item-value="id" v-model="event" label="Event" outlined></v-select>
      </div>
    </v-app-bar>

    <v-content>
      <router-view/>
    </v-content>
    <v-snackbar v-model="snackbar_open">
      {{ snackbar_text }}
      <v-btn color="pink" text @click="$store.commit('close_snackbar')">Close</v-btn>
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
    selected_event: {},
    show_hotel: false,
    show_event_settings: false,
  }),
  computed: {
    ...mapGetters([
      'snackbar_text',
      'initial_setup',
      'user',
      'logged_in',
      'events',
    ]),
    snackbar_open: {
      get() {
        return this.$store.state.snackbar.snackbar;
      },
      set(value) {
        if (!value) {
          this.$store.commit('close_snackbar');
        }
      },
    },
    event: {
      get() {
        return this.$store.state.events.event;
      },
      set(value) {
        const self = this;
        this.events.forEach((el) => {
          if (el.id === value) {
            self.$store.commit('set_event', el);
          }
        });
      },
    },
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
    updateMenus() {
      this.show_hotel = this.checkPermission('hotels.read');
      this.show_event_settings = this.checkPermission('event.read', this.event.id);
    },
  },
  watch: {
    user() {
      const self = this;
      this.$store.dispatch('get_events').then(() => {
        self.updateMenus();
      });
    },
    event() {
      this.updateMenus();
    },
  },
};
</script>
