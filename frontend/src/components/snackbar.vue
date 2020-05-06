<template>
  <v-snackbar v-model="snackbar_open">
    {{ snackbar_text }}
    <v-btn color="pink" text @click="$store.commit('close_snackbar')">Close</v-btn>
  </v-snackbar>
</template>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'snackbar',
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
};
</script>

<style scoped>

</style>
