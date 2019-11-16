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
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
          <v-card-title>
              Create new room
          </v-card-title>
          <v-card-text>
            <v-form>
              <v-text-field label="Name" v-model="hotel_room.name"></v-text-field>
              <v-text-field label="Description" v-model="hotel_room.description"></v-text-field>
              <v-checkbox label="Disable Autofill?" v-model="hotel_room.disable_autofill"></v-checkbox>
              <!-- Room Block -->
              <!-- Room Location -->
              <v-btn type="submit" @click.prevent="add_hotel_room" hidden="true"></v-btn>
            </v-form>
        </v-card-text>
        <v-card-actions>
            <v-btn type="submit" @click.prevent="add_hotel_room">Add</v-btn>
        </v-card-actions>
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
    hotel_room: {
      name: '',
      description: '',
      disable_autofill: false,
    },
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
    add_hotel_room() {
      const self = this;
      self.loading = true;
      self.hotel_rooms.push(self.room_night);
      self.post('/api/hotels/hotel_room', {
        event: self.event.id,
        hotel_rooms: self.hotel_rooms,
      }).then((res) => {
        self.loading = false;
        if (res.success) {
          self.hotel_room.name = '';
          self.$store.commit('open_snackbar', 'Room Added.');
          self.$asyncComputed.hotel_rooms.update();
        } else {
          self.$store.commit('open_snackbar', `Failed to add Room: ${res.reason}`);
        }
      });
    },
  },
};
</script>
