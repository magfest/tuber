<template>
  <div>
    <div>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Hotel Settings</v-card-title>
        <v-card-text>
            <h3>Room Nights</h3>
            <v-data-table show-select item-key="id" v-model="selected" :headers="headers" :items="room_nights">
                <template v-slot:item.restricted="{ item }">
                    <v-icon>
                        {{ item.restricted ? "check_box" : "check_box_outline_blank" }}
                    </v-icon>
                </template>
            </v-data-table>
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
    headers: [
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
            self.get('/api/hotels/settings', {
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
  },
  mounted() {
  },
  methods: {
    add_room_night() {
      const self = this;
      self.loading = true;
      self.room_nights.push(self.room_night);
      self.post('/api/hotels/settings', {
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
      });
    },
    delete_room_nights() {
      const self = this;
      this.selected.forEach((item) => {
        const idx = self.room_nights.indexOf(item);
        self.room_nights.splice(idx, 1);
      });
      self.post('/api/hotels/settings', {
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
      });
    },
  },
};
</script>
