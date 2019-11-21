<template>
  <v-container>
    <v-row>
      <v-col cols=3>
        <v-card class="mb-2">
          <v-card-title>Room Filters</v-card-title>
          <v-card-text>
            Hello
          </v-card-text>
        </v-card>
        <v-card>
          <v-card-title>Weights</v-card-title>
          <v-card-text>
            <div v-for="(val, key) in weights" :key="key">
              <v-slider :label="key" dense v-model="weights[key]" min="0" max="10" step="0.1"></v-slider>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols=6>
        <v-card class="mb-2" v-for="(room, room_id) in rooms" :key="room_id" @click="select_room($event, room_id)" :color="selected_rooms.includes(room_id) ? 'accent' : ''">
          <v-card-title>Room {{ room_id }}</v-card-title>
          <v-card-text>
            <v-text-field dense label="Room Notes" v-model="room.notes"></v-text-field>
            <v-card v-for="roommate in room.roommates" :key="roommate" @click.stop="select_roommate(roommate)" :color="selected_roommates.includes(roommate) ? 'accent' : ''">
              <v-card-text v-if="requests.hasOwnProperty(roommate)">
                {{ requests[roommate].name }}
              </v-card-text>
            </v-card>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols=3>
        <v-card>
          <v-card-title>Search</v-card-title>
          <v-card-text>
            <v-text-field dense clearable label="Search for People" append-icon="search" v-model="roommate_search"></v-text-field>
            <v-card v-for="match in filtered_matches" :key="match.id" @click="select_roommate(match.id)" :color="selected_roommates.includes(match.id) ? 'accent' : ''">
              <v-card-text v-if="requests.hasOwnProperty(match.id)">
                {{ requests[match.id].name }}
              </v-card-text>
            </v-card>
          </v-card-text>
          <v-card-actions>
            <v-btn :disabled="selected_rooms.length !== 1 || selected_roommates.length === 0" @click="assign_to_room">Assign</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
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
    hotkey_listener: null,
    selected_roommates: [],
    selected_rooms: [],
    loading: false,
    num_workers: 5,
    workers_initialized: false,
    workers: {},
    workers_busy: false,
    weights_dirty: false,
    weights: {
      room_nights: 4.0,
      roommates: 5.0,
      department: 3.0,
      gender: 1.0,
      noise: 1.0,
      smoke: 1.0,
      sleep_time: 1.0,
    },
    rooms: {
      1: {
        roommates: [
          2496,
        ],
        notes: 'This needs to be an atrium room.',
      },
      2: {
        roommates: [],
        notes: '',
      },
      3: {
        roommates: [],
        notes: '',
      },
      4: {
        roommates: [],
        notes: '',
      },
    },
    roommate_search: '',
  }),
  computed: {
    ...mapGetters([
      'event',
      'user',
    ]),
    prospective_roommates() {
      if (this.selected_rooms.length === 1) {
        return this.rooms[this.selected_rooms].roommates;
      }
      if (this.selected_roommates.length > 0) {
        return this.selected_roommates;
      }
      return [];
    },
    filtered_matches() {
      const results = [];
      if (this.selected_roommates.length > 0) {
        for (let i = 0; i < this.selected_roommates.length; i += 1) {
          results.push({
            id: this.selected_roommates[i],
          });
        }
      }
      let search = '';
      if (this.roommate_search !== null) {
        search = this.roommate_search.toLowerCase();
      }
      for (let i = 0; i < this.matches.length; i += 1) {
        if (this.requests[this.matches[i].id].name.toLowerCase().includes(search)) {
          let found = false;
          const roomIDs = Object.keys(this.rooms);
          for (let j = 0; j < roomIDs.length; j += 1) {
            if (this.rooms[roomIDs[j]].roommates.includes(this.matches[i].id)) {
              found = true;
              break;
            }
          }
          if (!found) {
            if (!this.selected_roommates.includes(this.matches[i].id)) {
              results.push(this.matches[i]);
              if (results.length >= 10) {
                return results;
              }
            }
          }
        }
      }
      return results;
    },
  },
  asyncComputed: {
    matches: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          if (!self.workers_initialized) {
            resolve([]);
          }
          let remaining = self.num_workers;
          const results = [];
          function complete(msg) {
            if (msg.data[0] !== 'searchdone') {
              return;
            }
            results.push(...msg.data[1]);
            remaining -= 1;
            if (remaining === 0) {
              results.sort((a, b) => ((a.weight > b.weight) ? -1 : 1));
              resolve(results);
            }
          }
          for (let i = 0; i < self.num_workers; i += 1) {
            self.workers[i].onmessage = complete;
            self.workers[i].postMessage(['searchRequests', self.prospective_roommates]);
          }
        });
      },
      default: [],
    },
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
    requests: {
      get() {
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
                resolve({});
              }
            }).catch(() => {
              self.$store.commit('open_snackbar', 'Failed to load requests.');
            });
          } else {
            resolve({});
          }
        });
      },
      default: {},
    },
  },
  beforeDestroy() {
    document.removeEventListener('keydown', this.hotkey_listener);
  },
  mounted() {
    this.hotkey_listener = document.addEventListener('keydown', this.hotkey);

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
          const ida = parseInt(badges[i], 10);
          const a = requests[ida];
          const nightsa = a.room_nights;
          self.edges[ida] = {};
          for (let j = 0; j < others.length; j += 1) {
            const request = others[j];
            if (request !== badges[i]) {
              let edge = 1;
              const idb = parseInt(request, 10);
              const b = requests[idb];
              const nightsb = b.room_nights;
              const differentNights = nightsa.filter(x => !nightsb.includes(x)).concat(nightsb.filter(x => !nightsa.includes(x)));
              if (differentNights.length > 0) {
                edge -= (weights.room_nights * differentNights.length);
              }

              if (a.requested_roommates.includes(idb) && b.requested_roommates.includes(ida)) {
                edge += weights.roommates;
              } else if (a.requested_roommates.includes(idb) || b.requested_roommates.includes(ida)) {
                edge += (weights.roommates / 2);
              }

              if (a.prefer_department) {
                if (b.departments.includes(a.preferred_department)) {
                  edge += (weights.department / 2);
                }
              }
              if (b.prefer_department) {
                if (a.departments.includes(b.preferred_department)) {
                  edge += (weights.department / 2);
                }
              }

              if (a.prefer_single_gender && b.prefer_single_gender) {
                if (a.preferred_gender === b.preferred_gender) {
                  edge += weights.gender;
                }
              }

              if (a.noise_level !== null && b.noise_level !== null) {
                edge += weights.noise * Math.abs(a.noise_level - b.noise_level) + 0.5;
              }

              if (a.smoke_sensitive || b.smoke_sensitive) {
                if (a.smoke_sensitive !== b.smoke_sensitive) {
                  edge -= weights.smoke;
                }
              }

              if (a.sleep_time !== null && b.sleep_time !== null) {
                let diff = Math.abs(a.sleep_time - b.sleep_time);
                if (diff > 5) {
                  diff = 12 - diff;
                }
                edge -= weights.sleep_time * (diff / 6) + 0.5;
              }

              if (a.antirequested_roommates.includes(idb) || b.antirequested_roommates.includes(idb)) {
                edge = 0;
              }
              self.edges[ida][idb] = edge;
            }
          }
        }
        self.postMessage(['loadingdone']);
      }

      function searchRequests(badges) {
        if (self.edges === undefined) {
          return;
        }
        const all = Object.keys(self.edges);
        const results = [];
        let i;
        let j;
        for (i = 0; i < all.length; i += 1) {
          if (badges.includes(parseInt(all[i], 10))) {
            continue;
          }
          let weight = 1;
          for (j = 0; j < badges.length; j += 1) {
            weight *= self.edges[all[i]][badges[j]];
          }
          results.push({ id: parseInt(all[i], 10), weight });
        }
        self.postMessage(['searchdone', results]);
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
    this.workers_initialized = true;
  },
  methods: {
    hotkey(event) {
      if (event.key === 'Escape') {
        this.selected_roommates = [];
        this.selected_rooms = [];
      } else if (event.key === 'a' && event.altKey) {
        this.assign_to_room();
      } else if (event.key === 'Delete') {
        this.delete_room();
      } else if (event.key === 'n' && event.altKey) {
        this.add_room();
      } else if ('!@#$%^&*()-+'.includes(event.key) && event.shiftKey && event.ctrlKey) {
        const idx = '!@#$%^&*()-+'.indexOf(event.key);
        this.select_roommate(this.filtered_matches[idx].id);
      }
    },
    add_room() {
      this.$set(this.rooms, 10, { roommates: [] });
      this.select_room(null, 10);
    },
    delete_room() {
      for (let i = 0; i < this.selected_rooms.length; i += 1) {
        delete this.rooms[this.selected_rooms[i]];
      }
      this.selected_rooms = [];
    },
    select_roommate(roommate) {
      if (this.selected_roommates.includes(roommate)) {
        const idx = this.selected_roommates.indexOf(roommate);
        this.selected_roommates.splice(idx, 1);
      } else {
        this.selected_roommates.push(roommate);
      }
    },
    select_room(event, room) {
      if (this.selected_rooms.includes(room)) {
        const idx = this.selected_rooms.indexOf(room);
        this.selected_rooms.splice(idx, 1);
        return;
      }
      if (event !== null && !event.shiftKey) {
        this.selected_rooms = [];
      }
      this.selected_rooms.push(room);
    },
    assign_to_room() {
      if (this.selected_rooms.length === 1) {
        for (let i = 0; i < this.selected_roommates.length; i += 1) {
          if (!this.rooms[this.selected_rooms[0]].roommates.includes(this.selected_roommates[i])) {
            this.rooms[this.selected_rooms[0]].roommates.push(this.selected_roommates[i]);
          }
        }
        this.selected_roommates = [];
      }
    },
    generate_weights() {
      const self = this;
      return new Promise((resolve) => {
        self.workers_busy = true;
        let remaining = self.num_workers;
        const keys = Object.keys(self.requests);
        const num = keys.length;
        function complete() {
          remaining -= 1;
          if (remaining === 0) {
            self.workers_busy = false;
            if (self.weights_dirty) {
              self.weights_dirty = false;
              resolve(self.generate_weights());
            } else {
              self.$asyncComputed.matches.update();
              resolve();
            }
          }
        }
        for (let i = 0; i < self.num_workers; i += 1) {
          const start = Math.min(i * (Math.floor(num / self.num_workers) + ((num % self.num_workers !== 0) ? 1 : 0)), num);
          const end = Math.min(num, start + Math.floor(num / self.num_workers) + ((num % self.num_workers !== 0) ? 1 : 0));
          if (start === end) {
            complete();
            continue;
          }
          self.workers[i].onmessage = complete;
          self.workers[i].postMessage(['loadRequests', keys.slice(start, end), self.requests, self.weights]);
        }
      });
    },
  },
  watch: {
    requests() {
      if (this.workers_busy) {
        this.weights_dirty = true;
      } else {
        this.generate_weights();
      }
    },
    weights: {
      handler() {
        if (this.workers_busy) {
          this.weights_dirty = true;
        } else {
          this.generate_weights();
        }
      },
      deep: true,
    },
  },
};
</script>
