<template>
  <div>
    <div>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Hotel Rooms</v-card-title>

      </v-card>
      <br>
      <div v-for="hotelRoom in hotel_rooms" :key="hotelRoom.id">
        <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
          <v-card-title>{{ hotelRoom.name }}</v-card-title>
          <v-card-text>
            {{ hotelRoom.description }}
          </v-card-text>
          <v-card-actions>
            <v-btn @click="delete_hotel_room">Delete</v-btn>
          </v-card-actions>
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
    },
    num_workers: 4,
    workers: {},
    weights: {
      room_nights: 1.0 / 6,
      roommates: 1.0,
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
            }).catch(() => {
              self.$store.commit('open_snackbar', 'Failed to get hotel rooms.');
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
            }).catch(() => {
              self.$store.commit('open_snackbar', 'Failed to get room nights.');
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
            }).catch(() => {
              self.$store.commit('open_snackbar', 'Failed to get room blocks.');
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
            }).catch(() => {
              self.$store.commit('open_snackbar', 'Failed to get room locations.');
            });
          } else {
            resolve([]);
          }
        });
      },
      default: [],
    },
    requests() {
      const self = this;
      return new Promise((resolve) => {
        if (self.event.id) {
          self.get('/api/hotels/all_requests', {
            event: self.event.id,
          }).then((response) => {
            if (response.success) {
              resolve(response.requests);
            } else {
              self.$store.commit('open_snackbar', 'Failed to load requests.');
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
    /* eslint-disable no-restricted-globals, no-console */
    function createWorker(fn) {
      const blob = new Blob(['self.onmessage = ', fn.toString()], { type: 'text/javascript' });
      const url = URL.createObjectURL(blob);
      return new Worker(url);
    }

    function worker(e) {
      function loadRequests(badges, requests, weights) {
        self.edges = {};
        const others = Object.keys(requests);
        for (let i = 0; i < badges.length; i += 1) {
          self.edges[badges[i]] = {};
          for (let j = 0; j < others.length; j += 1) {
            const request = others[j];
            if (request !== badges[i]) {
              let edge = 1;
              const nightsa = requests[badges[i]].room_nights;
              const nightsb = requests[request].room_nights;
              const differentNights = nightsa.filter(x => !nightsb.includes(x)).concat(nightsb.filter(x => !nightsa.includes(x)));
              if (differentNights.length > 0) {
                edge -= (weights.room_nights * differentNights.length);
              }

              if (requests[badges[i]].requested_roommates.includes(request) && requests[request].requested_roommates.includes(badges[i])) {
                edge += (weights.roommates);
              } else if (requests[badges[i]].requested_roommates.includes(request) || requests[request].requested_roommates.includes(badges[i])) {
                edge += (weights.roommates / 2);
              }

              if (requests[badges[i]].antirequested_roommates.includes(request) || requests[request].antirequested_roommates.includes(badges[i])) {
                edge = 0;
              }
              self.edges[badges[i]][request] = edge;
            }
          }
        }
      }

      function searchRequests(badges) {
        console.log(badges);
        console.log(self.value);
      }

      if (e.data[0] === 'loadRequests') {
        loadRequests(e.data[1], e.data[2], e.data[3]);
      }
      if (e.data[0] === 'searchRequests') {
        searchRequests(e.data[1]);
      }
    }
    /* eslint-enable */

    for (let i = 0; i < this.num_workers; i += 1) {
      this.workers[i] = createWorker(worker);
    }
  },
  methods: {
    add_hotel_room() {
      const self = this;
      self.loading = true;
      self.hotel_rooms.push(self.hotel_room);
      self.post('/api/hotels/hotel_room', {
        event: self.event.id,
        hotel_rooms: self.hotel_rooms,
      }).then((res) => {
        self.loading = false;
        if (res.success) {
          self.hotel_room.name = '';
          self.hotel_room.description = '';
          self.$store.commit('open_snackbar', 'Room Added.');
          self.$asyncComputed.hotel_rooms.update();
        } else {
          self.$store.commit('open_snackbar', `Failed to add Room: ${res.reason}`);
        }
      }).catch(() => {
        self.$store.commit('open_snackbar', 'Failed to add hotel room.');
      });
    },
    delete_hotel_room() {

    },
  },
  watch: {
    requests(value) {
      const keys = Object.keys(value);
      const num = keys.length;
      for (let i = 0; i < this.num_workers; i += 1) {
        const start = Math.min(i * (Math.floor(num / this.num_workers) + ((num % this.num_workers !== 0) ? 1 : 0)), num);
        const end = Math.min(num, start + Math.floor(num / this.num_workers) + ((num % this.num_workers !== 0) ? 1 : 0));
        if (start === end) {
          break;
        }
        this.workers[i].postMessage(['loadRequests', keys.slice(start, end), value, this.weights]);
      }
    },
  },
};
</script>
