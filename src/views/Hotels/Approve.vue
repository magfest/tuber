<template>
  <div>
    <div>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Hotel Requests</v-card-title>
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
  name: 'RequestApprove',
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
