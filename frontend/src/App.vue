<template>
  <v-app>
    <Navbar/>
    <v-content>
      <transition name="slide">
        <router-view/>
      </transition>
    </v-content>
    <snackbar/>
  </v-app>
</template>

<script>
import Navbar from './components/navbar/navbar.vue';
import Snackbar from './components/snackbar.vue';

export default {
  name: 'App',
  components: { Snackbar, Navbar },
  created() {
    this.$vuetify.theme.secondary = '#000000';
  },
};
</script>
