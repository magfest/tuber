<template>
  <div>
    <div>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Room Night Settings</v-card-title>
        <v-card-text>
          <v-data-table show-select item-key="id" v-model="selected" :headers="room_nights_headers" :items="room_nights">
            <template v-slot:item.restricted="{ item }">
              <v-icon>
                {{ item.restricted ? "check_box" : "check_box_outline_blank" }}
              </v-icon>
            </template>
          </v-data-table>
          <br>
        </v-card-text>
        <v-card-actions>
            <v-btn @click="delete_room_nights">Delete</v-btn>
        </v-card-actions>
      </v-card>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
          <v-card-title>
              Create new room night
          </v-card-title>
          <v-card-text>
            <v-form>
                <v-text-field label="Name" v-model="room_night.name"></v-text-field>
                <v-checkbox label="Restricted" v-model="room_night.restricted"></v-checkbox>
                <v-text-field label="Restriction Type" v-if="room_night.restricted" v-model="room_night.restriction_type"></v-text-field>
                <v-btn type="submit" @click.prevent="add_room_night" hidden="true"></v-btn>
            </v-form>
        </v-card-text>
        <v-card-actions>
            <v-btn type="submit" @click.prevent="add_room_night">Add</v-btn>
        </v-card-actions>
      </v-card>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Room Block Settings</v-card-title>
        <v-card-text>
          <v-data-table show-select item-key="id" v-model="selected" :headers="room_blocks_headers" :items="room_blocks">

          </v-data-table>
          <br>
        </v-card-text>
        <v-card-actions>
            <v-btn @click="delete_room_blocks">Delete</v-btn>
        </v-card-actions>
      </v-card>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
          <v-card-title>
              Create new room block
          </v-card-title>
          <v-card-text>
            <v-form>
              <v-text-field label="Name" v-model="room_block.name"></v-text-field>
              <v-text-field label="Description" v-model="room_block.description"></v-text-field>
              <v-btn type="submit" @click.prevent="add_room_block" hidden="true"></v-btn>
            </v-form>
        </v-card-text>
        <v-card-actions>
            <v-btn type="submit" @click.prevent="add_room_block">Add</v-btn>
        </v-card-actions>
      </v-card>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Room Location Settings</v-card-title>
        <v-card-text>
          <v-data-table show-select item-key="id" v-model="selected" :headers="room_locations_headers" :items="room_locations">

          </v-data-table>
          <br>
        </v-card-text>
        <v-card-actions>
            <v-btn @click="delete_room_locations">Delete</v-btn>
        </v-card-actions>
      </v-card>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
          <v-card-title>
              Create new room location
          </v-card-title>
          <v-card-text>
            <v-form>
              <v-text-field label="Name" v-model="room_location.name"></v-text-field>
              <v-text-field label="Address" v-model="room_location.address"></v-text-field>
              <v-btn type="submit" @click.prevent="add_room_location" hidden="true"></v-btn>
            </v-form>
        </v-card-text>
        <v-card-actions>
            <v-btn type="submit" @click.prevent="add_room_location">Add</v-btn>
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
  name: 'HotelSettings',
  components: {
  },
  data: () => ({
    loading: false,
    selected: [],
    room_night: {
      name: '',
      restricted: false,
      restriction_type: '',
    },
    room_block: {
      name: '',
      description: '',
    },
    room_location: {
      name: '',
      address: '',
    },
    room_nights_headers: [
      {
        text: 'Name',
        value: 'name',
      },
      {
        text: 'Restricted',
        value: 'restricted',
        align: 'center',
      },
      {
        text: 'Restriction Type',
        value: 'restriction_type',
      },
    ],
    room_blocks_headers: [
      {
        text: 'Name',
        value: 'name',
      },
      {
        text: 'Description',
        value: 'description',
      },
    ],
    room_locations_headers: [
      {
        text: 'Name',
        value: 'name',
      },
      {
        text: 'Address',
        value: 'address',
      },
    ],
  }),
  computed: {
    ...mapGetters([
      'event',
    ]),
  },
  asyncComputed: {
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
              self.$store.commit('open_snackbar', 'Failed to retrieve hotel settings.');
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
              self.$store.commit('open_snackbar', 'Failed to get hotel room blocks.');
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
              self.$store.commit('open_snackbar', 'Failed to get hotel room locations.');
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
    add_room_night() {
      const self = this;
      self.loading = true;
      self.room_nights.push(self.room_night);
      self.post('/api/hotels/settings/room_night', {
        event: self.event.id,
        room_nights: self.room_nights,
      }).then((res) => {
        self.loading = false;
        if (res.success) {
          self.room_night.name = '';
          self.$store.commit('open_snackbar', 'Room Night Added.');
          self.$asyncComputed.room_nights.update();
        } else {
          self.$store.commit('open_snackbar', `Failed to add Room Night: ${res.reason}`);
        }
      }).catch(() => {
        self.$store.commit('open_snackbar', 'Failed to update hotel settings.');
      });
    },
    delete_room_nights() {
      const self = this;
      this.selected.forEach((item) => {
        const idx = self.room_nights.indexOf(item);
        self.room_nights.splice(idx, 1);
      });
      self.post('/api/hotels/settings/room_night', {
        event: self.event.id,
        room_nights: self.room_nights,
      }).then((res) => {
        if (res.success) {
          self.$store.commit('open_snackbar', 'Room Nights Deleted.');
          self.$asyncComputed.room_nights.update();
        } else {
          self.$store.commit('open_snackbar', 'Failed to delete Room Nights.');
          self.$asyncComputed.room_nights.update();
        }
      }).catch(() => {
        self.$store.commit('open_snackbar', 'Failed to check update hotel settings.');
      });
    },
    add_room_block() {
      const self = this;
      self.loading = true;
      self.room_blocks.push(self.room_block);
      self.post('/api/hotels/settings/room_block', {
        event: self.event.id,
        room_blocks: self.room_blocks,
      }).then((res) => {
        self.loading = false;
        if (res.success) {
          self.room_block.name = '';
          self.room_block.description = '';
          self.$store.commit('open_snackbar', 'Room Block Added.');
          self.$asyncComputed.room_block.update();
        } else {
          self.$store.commit('open_snackbar', `Failed to add Room Block: ${res.reason}`);
        }
      });
    },
    delete_room_blocks() {
      const self = this;
      this.selected.forEach((item) => {
        const idx = self.room_blocks.indexOf(item);
        self.room_blocks.splice(idx, 1);
      });
      self.post('/api/hotels/settings/room_block', {
        event: self.event.id,
        room_blocks: self.room_blocks,
      }).then((res) => {
        if (res.success) {
          self.$store.commit('open_snackbar', 'Room Blocks Deleted.');
          self.$asyncComputed.room_blocks.update();
        } else {
          self.$store.commit('open_snackbar', `Failed to delete Room Blocks: ${res.reason}`);
          self.$asyncComputed.room_blocks.update();
        }
      });
    },
    add_room_location() {
      const self = this;
      self.loading = true;
      self.room_locations.push(self.room_location);
      self.post('/api/hotels/settings/room_location', {
        event: self.event.id,
        room_locations: self.room_locations,
      }).then((res) => {
        self.loading = false;
        if (res.success) {
          self.room_location.name = '';
          self.room_location.address = '';
          self.$store.commit('open_snackbar', 'Room Location Added.');
          self.$asyncComputed.room_location.update();
        } else {
          self.$store.commit('open_snackbar', `Failed to add Room Location: ${res.reason}`);
        }
      });
    },
    delete_room_locations() {
      const self = this;
      this.selected.forEach((item) => {
        const idx = self.room_locations.indexOf(item);
        self.room_locations.splice(idx, 1);
      });
      self.post('/api/hotels/settings/room_location', {
        event: self.event.id,
        room_locations: self.room_locations,
      }).then((res) => {
        if (res.success) {
          self.$store.commit('open_snackbar', 'Room Location Deleted.');
          self.$asyncComputed.room_locations.update();
        } else {
          self.$store.commit('open_snackbar', `Failed to delete Room Location: ${res.reason}`);
          self.$asyncComputed.room_locations.update();
        }
      });
    },
  },
};
</script>
