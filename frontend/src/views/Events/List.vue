<template>
  <div>
      <br>
      <v-dialog v-model="edit_modal_active" max-width="1200">
        <event-form v-model="event" @input="edit_modal_active=false" @saved="$asyncComputed.events.update()"></event-form>
      </v-dialog>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Events</v-card-title>
        <v-card-text>
          <v-data-table :headers="headers" :items="events">
            <template v-slot:item.name="{ item }">
              <div @click="edit_event(item)" style="cursor: pointer; color: blue">{{ item.name }}</div>
            </template>
            <template v-slot:item.delete="{ item }">
              <v-icon style="cursor: pointer" @click="delete_event(item)">delete</v-icon>
            </template>
          </v-data-table>
          <v-btn @click="edit_event(Object.assign({}, default_event))">Add</v-btn>
        </v-card-text>
      </v-card>
    </div>
</template>

<style>
</style>

<script>
import EventForm from './Form.vue';
import { mapAsyncDump } from '../../mixins/rest';

export default {
  name: 'event-list',
  components: {
    EventForm,
  },
  data: () => ({
    loading: false,
    edit_modal_active: false,
    event: {},
    default_event: {
      name: 'New Event',
      description: '',
    },
    headers: [
      {
        text: 'Name',
        value: 'name',
      },
      {
        text: 'Description',
        value: 'description',
      },
      {
        text: 'Delete',
        value: 'delete',
      },
    ],
  }),
  asyncComputed: {
    ...mapAsyncDump([
      'events',
    ]),
  },
  methods: {
    delete_event(event) {
      this.loading = true;
      this.remove('events', event).then(() => {
        this.loading = false;
        this.notify(`Event ${event.name} deleted successfully.`);
      }).catch(() => {
        this.loading = false;
        this.notify(`Failed to delete event ${event.name}`);
      });
    },
    edit_event(event) {
      this.event = event;
      this.edit_modal_active = true;
    },
  },
  watch: {
    events() {
      this.$store.dispatch('get_events');
    },
  },
};
</script>
