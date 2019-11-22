<template>
  <v-container>
    <v-dialog v-model="open_room_modal" width="700">
      <v-card :loading="loading">
        <v-card-title class="headline grey lighten-2" primary-title>Edit {{ active_room.name ? active_room.name : "Room " + active_room.id }}</v-card-title>
        <v-card-text>
          <v-form>
            <v-text-field label="Name" v-model="active_room.name"></v-text-field>
            <v-text-field label="Notes" v-model="active_room.notes"></v-text-field>
            <v-text-field label="Messages" v-model="active_room.messages"></v-text-field>
            <v-select label="Hotel Block" :items="room_blocks" item-value="id" item-text="name" v-model="active_room.hotel_block"></v-select>
            <v-select label="Hotel Location" :items="room_locations" item-value="id" item-text="name" v-model="active_room.hotel_location"></v-select>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn left @click="open_room_modal = false">Close</v-btn>
          <v-btn color="primary" text @click="save_room(active_room)">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog v-model="open_roommate_modal" width="700">
      <v-card :loading="loading">
        <v-card-title class="headline grey lighten-2" primary-title>Edit {{ active_roommate.name }}</v-card-title>
        <v-card-text>
          <request-short ref="reqDialog" :badge_id="active_roommate.id"></request-short>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn left @click="open_roommate_modal = false">Close</v-btn>
          <v-btn color="primary" text @click="save_roommate()">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-row>
      <v-col cols=3>
        <div style="position: fixed; width: 275px">
          <v-card class="mb-2">
            <v-card-title>Room Filters</v-card-title>
            <v-card-text>
              <v-checkbox v-model="hide_completed" label="Hide Completed"></v-checkbox>
              <v-btn @click="reset_minimized">Restore Minimized</v-btn>
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
        </div>
      </v-col>
      <v-col cols=6>
        <v-card class="mb-2" v-for="room in filtered_rooms" :key="room.id" :color="selected_rooms.includes(room.id.toString()) ? '#BBDEFB' : room.completed ? '#B2DFDB' : ''">
          <v-card-title @click.self="select_room($event, room.id)"><v-icon @click.stop.prevent="room_modal(room)">edit</v-icon>{{ room.name ? room.name : "Room " + room.id }}<v-spacer></v-spacer><v-checkbox dense label="Complete" @change="save_room(room)" v-model="room.completed"></v-checkbox><v-spacer></v-spacer><v-btn @click="room.minimized=true">Minimize</v-btn></v-card-title>
          <v-card-text>
            <p>{{ room.notes }}</p>
            <v-card v-for="(nights, roommate) in roommates[room.id]" :key="roommate" @click.stop="select_roommate(roommate)" :color="selected_roommates.includes(roommate.toString()) ? '#BBDEFB' : ''">
              <v-card-text v-if="requests.hasOwnProperty(roommate)">
                <v-icon @click.stop.prevent="roommate_modal(requests[roommate])">edit</v-icon><v-icon @click.stop.prevent="assign_to_room([requests[roommate].id], room.id, [])">delete</v-icon>{{ requests[roommate].name }} <span v-for="night in nights" :key="night">{{ room_nights[night].name.slice(0,2) }} </span>
              </v-card-text>
            </v-card>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols=3>
        <div style="position: fixed; width: 275px">
          <v-card>
            <v-card-text>
              <v-text-field dense clearable label="Search for People" append-icon="search" v-model="roommate_search"></v-text-field>
              <v-card v-for="match in filtered_matches" :key="match.id" @click="select_roommate(match.id)" :color="selected_roommates.includes(match.id) ? '#BBDEFB' : ''">
                <v-card-text class="pa-1" v-if="requests.hasOwnProperty(match.id)">
                  {{ requests[match.id].name }} {{ match.weight ? "("+Math.round(match.weight)+")" : "" }} <br> <v-icon @click.stop.prevent="roommate_modal(requests[match.id])">edit</v-icon><span v-for="night in [...requests[match.id].room_nights].sort()" :key="night">{{ room_nights[night].name.slice(0,2) }} </span>
                </v-card-text>
              </v-card>
            </v-card-text>
            <v-card-actions>
              <v-btn left @click="add_room()">Add Room</v-btn><v-btn :disabled="selected_rooms.length !== 1 || selected_roommates.length === 0" @click="assign_to_room(null, null, null)">Assign</v-btn>
            </v-card-actions>
          </v-card>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';
import RequestShort from './RequestShort.vue';

export default {
  name: 'HotelAssign',
  components: {
    RequestShort,
  },
  data: () => ({
    active_room: {},
    open_room_modal: false,
    active_roommate: {},
    open_roommate_modal: false,
    hide_completed: true,
    completed_rooms: {},
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
    roommate_search: '',
  }),
  computed: {
    ...mapGetters([
      'event',
      'user',
    ]),
    roommates() {
      const rooms = {};
      const badges = Object.keys(this.assignments);
      for (let i = 0; i < badges.length; i += 1) {
        const roomNightIDs = Object.keys(this.assignments[badges[i]]);
        for (let j = 0; j < roomNightIDs.length; j += 1) {
          const assignedRooms = this.assignments[badges[i]][roomNightIDs[j]];
          for (let k = 0; k < assignedRooms.length; k += 1) {
            if (!Object.prototype.hasOwnProperty.call(rooms, assignedRooms[k])) {
              rooms[assignedRooms[k]] = {};
            }
            if (!Object.prototype.hasOwnProperty.call(rooms[assignedRooms[k]], badges[i])) {
              rooms[assignedRooms[k]][badges[i]] = [];
            }
            rooms[assignedRooms[k]][badges[i]].push(roomNightIDs[j]);
          }
        }
      }
      return rooms;
    },
    prospective_roommates() {
      let roommates = [];
      if (this.selected_rooms.length === 1) {
        if (Object.prototype.hasOwnProperty.call(this.roommates, this.selected_rooms[0])) {
          roommates = Object.keys(this.roommates[this.selected_rooms[0]]);
        }
      }
      if (this.selected_roommates.length > 0) {
        roommates.push(...this.selected_roommates);
      }
      return roommates;
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
        if (!Object.prototype.hasOwnProperty.call(this.requests, this.matches[i].id)) {
          continue;
        }
        if (this.requests[this.matches[i].id].name.toLowerCase().includes(search)) {
          let found = false;

          if (Object.prototype.hasOwnProperty.call(this.assignments, this.matches[i].id)) {
            const nightIDs = Object.keys(this.assignments[this.matches[i].id]);
            for (let j = 0; j < nightIDs.length; j += 1) {
              if (this.assignments[this.matches[i].id][nightIDs[j]].length > 0) {
                found = true;
                break;
              }
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
    filtered_rooms() {
      const rooms = [];
      for (let i = 0; i < this.rooms.length; i += 1) {
        if (this.rooms[i].completed && this.hide_completed) {
          continue;
        }
        if (Object.prototype.hasOwnProperty.call(this.rooms[i], 'minimized') && this.rooms[i].minimized) {
          continue;
        }
        rooms.push(this.rooms[i]);
      }
      rooms.sort((a, b) => ((a.id > b.id) ? 1 : -1));
      return rooms;
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
    rooms: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          if (self.event.id) {
            self.get('/api/hotels/hotel_room', {
              event: self.event.id,
            }).then((res) => {
              if (res.success) {
                for (let i = 0; i < res.hotel_rooms.length; i += 1) {
                  res.hotel_rooms[i].minimized = false;
                }
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
                const rn = {};
                for (let i = 0; i < res.room_nights.length; i += 1) {
                  rn[res.room_nights[i].id] = res.room_nights[i];
                }
                resolve(rn);
              } else {
                resolve({});
              }
            }).catch(() => {
              self.$store.commit('open_snackbar', 'Failed to get room nights.');
            });
          } else {
            resolve({});
          }
        });
      },
      default: {},
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
    assignments: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          if (self.event.id) {
            self.get('/api/hotels/room_assignments', {
              event: self.event.id,
            }).then((response) => {
              if (response.success) {
                resolve(response.room_assignments);
              } else {
                self.$store.commit('open_snackbar', 'Failed to load assignments.');
                resolve({});
              }
            }).catch(() => {
              self.$store.commit('open_snackbar', 'Failed to load assignments.');
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
              } else {
                edge += weights.room_nights;
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
          let antirequest = false;
          for (j = 0; j < badges.length; j += 1) {
            if (self.edges[all[i]][badges[j]] === 0) {
              antirequest = true;
            }
            weight += self.edges[all[i]][badges[j]];
          }
          if (antirequest) {
            weight = 0;
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
        this.assign_to_room(null, null, null);
      } else if (event.key === 'Delete') {
        this.delete_room(this.selected_rooms);
      } else if (event.key === 'n' && event.altKey) {
        this.add_room();
      } else if ('!@#$%^&*()-+'.includes(event.key) && event.shiftKey && event.ctrlKey) {
        const idx = '!@#$%^&*()-+'.indexOf(event.key);
        this.select_roommate(this.filtered_matches[idx].id);
      }
    },
    add_room() {
      const self = this;
      if (self.event.id) {
        self.post('/api/hotels/hotel_room', {
          event: self.event.id,
        }).then((res) => {
          if (res.success) {
            self.$asyncComputed.rooms.update();
            self.select_room(null, res.room.id);
          } else {
            self.$store.commit('open_snackbar', 'Failed to create hotel room.');
          }
        }).catch(() => {
          self.$store.commit('open_snackbar', 'Failed to create hotel room.');
        });
      }
    },
    delete_room(rooms) {
      const self = this;
      if (self.event.id) {
        self.dodelete('/api/hotels/hotel_room', {
          event: self.event.id,
          rooms,
        }).then((res) => {
          if (res.success) {
            self.$asyncComputed.rooms.update();
            self.$asyncComputed.assignments.update();
          } else {
            self.$store.commit('open_snackbar', 'Failed to delete hotel room.');
          }
        }).catch(() => {
          self.$store.commit('open_snackbar', 'Failed to delete hotel room.');
        });
      }
    },
    save_room(room) {
      const self = this;
      self.loading = true;
      if (self.event.id) {
        self.post('/api/hotels/hotel_room', {
          event: self.event.id,
          rooms: [room],
        }).then((res) => {
          if (res.success) {
            self.$asyncComputed.rooms.update();
            self.loading = false;
            self.open_room_modal = false;
            self.$store.commit('open_snackbar', `Room ${room.id} saved successfully.`);
          } else {
            self.$store.commit('open_snackbar', 'Failed to save hotel room.');
            self.loading = false;
          }
        }).catch(() => {
          self.$store.commit('open_snackbar', 'Failed to save hotel room.');
          self.loading = false;
        });
      }
    },
    save_roommate() {
      const self = this;
      self.loading = true;
      if (self.event.id) {
        self.$refs.reqDialog.save().then((res) => {
          if (res) {
            self.loading = false;
            self.open_roommate_modal = false;
            self.$asyncComputed.requests.update();
            self.$store.commit('open_snackbar', 'Request saved successfully.');
          } else {
            self.$store.commit('open_snackbar', 'Failed to save request.');
            self.loading = false;
          }
        }).catch(() => {
          self.$store.commit('open_snackbar', 'Failed to save request.');
          self.loading = false;
        });
      }
    },
    reset_minimized() {
      for (let i = 0; i < this.rooms.length; i += 1) {
        this.rooms[i].minimized = false;
      }
    },
    select_roommate(roommate) {
      if (this.selected_roommates.includes(roommate)) {
        const idx = this.selected_roommates.indexOf(roommate);
        this.selected_roommates.splice(idx, 1);
      } else {
        this.selected_roommates.push(roommate);
      }
      this.roommate_search = '';
    },
    select_room(event, room) {
      const roomID = room.toString();
      if (this.selected_rooms.includes(roomID)) {
        const idx = this.selected_rooms.indexOf(roomID);
        this.selected_rooms.splice(idx, 1);
        return;
      }
      if (event === null) {
        this.selected_rooms = [];
      } else if (!event.shiftKey) {
        this.selected_rooms = [];
      }
      this.selected_rooms.push(roomID);
    },
    assign_to_room(badges, roomID, roomNightIDs) {
      const self = this;
      if (badges === null) {
        if (this.selected_roommates.length > 0) {
          badges = this.selected_roommates;
        } else {
          return;
        }
      }
      if (roomID === null) {
        if (this.selected_rooms.length !== 1) {
          return;
        }
        [roomID] = this.selected_rooms;
      }
      if (self.event.id) {
        self.post('/api/hotels/room_assignments', {
          event: self.event.id,
          badges,
          room_nights: roomNightIDs,
          hotel_room: roomID,
        }).then((res) => {
          if (res.success) {
            self.$asyncComputed.assignments.update();
            this.selected_roommates = [];
          } else {
            self.$store.commit('open_snackbar', 'Failed to assign hotel room.');
          }
        }).catch(() => {
          self.$store.commit('open_snackbar', 'Failed to assign hotel room.');
        });
      }
    },
    room_modal(room) {
      this.active_room = room;
      this.open_room_modal = true;
    },
    roommate_modal(roommate) {
      this.active_roommate = roommate;
      this.open_roommate_modal = true;
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
