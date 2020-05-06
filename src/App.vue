<template>
  <v-app>
    <Navbar/>
    <v-content>
      <transition name="slide">
        <router-view/>
      </transition>
    </v-content>
    <v-snackbar v-model="snackbar_open">
      {{ snackbar_text }}
      <v-btn color="pink" text @click="$store.commit('close_snackbar')">Close</v-btn>
    </v-snackbar>
  </v-app>
</template>

<script>
import { mapGetters } from 'vuex';
import Navbar from './components/navbar/navbar.vue';

export default {
  name: 'App',
  components: { Navbar },
  computed: {
    ...mapGetters([
      'snackbar_text',
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
  },
  created() {
    this.$vuetify.theme.secondary = '#000000';
  },
};
</script>
