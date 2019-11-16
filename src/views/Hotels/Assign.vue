<template>
  <div>
    <div>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Hotel Rooms</v-card-title>

      </v-card>
      <br>
      <div v-for="hotelRoom in hotel_rooms" :key="hotelRoom.id">
        <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
          <v-card-title>{{ hotelRoom.name }}</v-card-title>

        </v-card>
        <br>
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
    hotel_rooms: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          if (self.event.id && self.user.id) {
            self.get('/api/hotels/hotel_room', {
              event: self.event.id,
              user: self.user.id,
            }).then((res) => {
              if (res.success) {
                resolve(res.hotel_rooms);
              } else {
                resolve([]);
              }
            });
          } else {
            resolve([]);
          }
        });
      },
      default: [],
    },
    room_nights: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          if (self.event.id) {
            self.get('/api/hotels/settings/room_night', {
              event: self.event.id,
            }).then((res) => {
              if (res.success) {
                resolve(res.room_nights);
              } else {
                resolve([]);
              }
            });
          } else {
            resolve([]);
          }
        });
      },
      default: [],
    },
    room_blocks: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          if (self.event.id) {
            self.get('/api/hotels/settings/room_block', {
              event: self.event.id,
            }).then((res) => {
              if (res.success) {
                resolve(res.room_blocks);
              } else {
                resolve([]);
              }
            });
          } else {
            resolve([]);
          }
        });
      },
      default: [],
    },
    room_locations: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          if (self.event.id) {
            self.get('/api/hotels/settings/room_location', {
              event: self.event.id,
            }).then((res) => {
              if (res.success) {
                resolve(res.room_locations);
              } else {
                resolve([]);
              }
            });
          } else {
            resolve([]);
          }
        });
      },
      default: [],
    },
  },
  mounted() {
  },
  methods: {
  },
};
</script>
