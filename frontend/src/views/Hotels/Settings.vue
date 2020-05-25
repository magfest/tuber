<template>
  <div>
    <div>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Room Night Settings</v-card-title>
        <v-card-text>
          <v-data-table show-select item-key="id" v-model="selected.room_nights" :headers="room_nights_headers" :items="room_nights">
            <template v-slot:item.restricted="{ item }">
              <v-icon>
                {{ item.restricted ? "check_box" : "check_box_outline_blank" }}
              </v-icon>
            </template>
            <template v-slot:item.hidden="{ item }">
              <v-icon>
                {{ item.hidden ? "check_box" : "check_box_outline_blank" }}
              </v-icon>
            </template>
          </v-data-table>
          <br>
        </v-card-text>
        <v-card-actions>
            <v-btn @click="remove_selected('room_nights')">Delete</v-btn>
        </v-card-actions>
      </v-card>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
          <v-card-title>
              Create new room night
          </v-card-title>
          <v-card-text>
            <v-form>
                <v-text-field label="Name" v-model="form.room_nights.name"></v-text-field>
                <v-checkbox label="Restricted" v-model="form.room_nights.restricted"></v-checkbox>
                <v-text-field label="Restriction Type" v-if="form.room_nights.restricted" v-model="form.room_nights.restriction_type"></v-text-field>
                <v-checkbox label="Hidden" v-model="form.room_nights.hidden"></v-checkbox>
            </v-form>
        </v-card-text>
        <v-card-actions>
            <v-btn type="submit" @click.prevent="add('room_nights')">Add</v-btn>
        </v-card-actions>
      </v-card>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Room Block Settings</v-card-title>
        <v-card-text>
          <v-data-table show-select item-key="id" v-model="selected.room_blocks" :headers="room_blocks_headers" :items="room_blocks">

          </v-data-table>
          <br>
        </v-card-text>
        <v-card-actions>
            <v-btn @click="remove_selected('room_blocks')">Delete</v-btn>
        </v-card-actions>
      </v-card>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
          <v-card-title>
              Create new room block
          </v-card-title>
          <v-card-text>
            <v-form>
              <v-text-field label="Name" v-model="form.room_blocks.name"></v-text-field>
              <v-text-field label="Description" v-model="form.room_blocks.description"></v-text-field>
            </v-form>
        </v-card-text>
        <v-card-actions>
            <v-btn type="submit" @click.prevent="add('room_blocks')">Add</v-btn>
        </v-card-actions>
      </v-card>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Room Location Settings</v-card-title>
        <v-card-text>
          <v-data-table show-select item-key="id" v-model="selected.room_locations" :headers="room_locations_headers" :items="room_locations">

          </v-data-table>
          <br>
        </v-card-text>
        <v-card-actions>
            <v-btn @click="remove_selected('room_locations')">Delete</v-btn>
        </v-card-actions>
      </v-card>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
          <v-card-title>
              Create new room location
          </v-card-title>
          <v-card-text>
            <v-form>
              <v-text-field label="Name" v-model="form.room_locations.name"></v-text-field>
              <v-text-field label="Address" v-model="form.room_locations.address"></v-text-field>
            </v-form>
        </v-card-text>
        <v-card-actions>
            <v-btn type="submit" @click.prevent="add('room_locations')">Add</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';
import { mapAsyncDump } from '../../mixins/rest';

export default {
  name: 'HotelSettings',
  components: {
  },
  data: () => ({
    loading: false,
    selected: {
      selected_room_blocks: [],
      selected_room_locations: [],
      selected_room_nights: [],
    },
    form: {
      room_nights: {
        name: '',
        restricted: false,
        restriction_type: '',
        hidden: false,
      },
      room_blocks: {
        name: '',
        description: '',
      },
      room_locations: {
        name: '',
        address: '',
      },
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
      {
        text: 'Hidden',
        value: 'hidden',
        align: 'center',
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
    ...mapAsyncDump([
      'room_nights',
      'room_blocks',
      'room_locations',
    ]),
  },
  methods: {
    add(entity) {
      const self = this;
      self.loading = true;
      self.save(entity, self.form[entity]).then(() => {
        self.loading = false;
        self.$asyncComputed[entity].update();
      }).catch(() => {
        self.loading = false;
      });
    },
    remove_selected(entity) {
      const self = this;
      const promises = [];
      self.loading = true;
      this.selected[entity].forEach((item) => {
        promises.push(self.remove(entity, item));
      });
      Promise.all(promises).then(() => {
        self.loading = false;
        self.$asyncComputed[entity].update();
      }).catch(() => {
        self.loading = false;
      });
    },
  },
};
</script>
