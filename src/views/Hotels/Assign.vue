<template>
  <div>
    <div>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Hotel Rooms</v-card-title>

      </v-card>
      <br>
      <div v-for="hotelRoom in hotelrooms" :key="hotelRoom.id">
        <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
          <v-card-title>{{ hotelRoom.name }}</v-card-title>

        </v-card>
      </div>
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
      'user',
    ]),
  },
  asyncComputed: {
    hotelrooms() {
      const self = this;
      return new Promise((resolve) => {
        if (self.event.id && self.user.id) {
          self.get('/api/hotels/hotel_room', {
            event: self.event.id,
            user: self.user.id,
          }).then((hotelRooms) => {
            if (hotelRooms.success) {
              resolve(hotelRooms.departments);
            } else {
              resolve([]);
            }
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
