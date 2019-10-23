<template>
  <div>
    <div>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Event Settings</v-card-title>
        <v-card-text>

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
  name: 'EventSettings',
  components: {
  },
  data: () => ({
    loading: false,
  }),
  computed: {
    ...mapGetters([
      'event',
    ]),
  },
  mounted() {
  },
  methods: {
  },
};
</script>
