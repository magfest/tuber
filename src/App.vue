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
        <span>2ber</span>
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <div>
        <v-select class="event-select" :items="events" :value="event" label="Event" outlined></v-select>
      </div>
    </v-app-bar>

    <v-content>
      <router-view/>
    </v-content>
    <v-snackbar v-model="snackbar">
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
    events: [
      'MAGFest 2019',
      'MAGStock 2019',
      'MAGWest 2020',
    ],
    event: 'MAGFest 2019',
  }),
  computed: {
    ...mapGetters([
      'snackbar',
      'snackbar_text',
    ]),
  },
  created() {
    this.$vuetify.theme.dark = true;
  },
};
</script>
