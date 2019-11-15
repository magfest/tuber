<template>
  <div>
    <div>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Hotel Rooms</v-card-title>
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
  name: 'HotelAssign',
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
  asyncComputer: {
    requests() {
      const self = this;
      return new Promise((resolve) => {
        if (self.event.id && self.user.id) {
          self.get('/api/hotels/requests', {
            event: self.event.id,
            user: self.user.id,
          }).then((depts) => {
            if (depts.success) {
              resolve(depts.departments);
            } else {
              resolve([]);
            }
          }).catch(() => {
            self.$store.commit('open_snackbar', 'Failed to load requests.');
          });
        } else {
          resolve([]);
        }
      });
    },
  },
  mounted() {
  },
  methods: {
  },
};
</script>
