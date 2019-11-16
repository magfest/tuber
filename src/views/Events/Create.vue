<template>
  <div>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="event_loading">
        <v-card-title>Create an event</v-card-title>
        <v-card-text>
          <v-form>
            <p>Describe your event:</p>
            <v-text-field label="Name" v-model="name" outlined></v-text-field>
            <v-text-field label="Description" v-model="description" outlined></v-text-field>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn outlined type="submit" @click.prevent="create_event">Submit</v-btn>
            </v-card-actions>
          </v-form>
        </v-card-text>
      </v-card>
    </div>
</template>

<style>
</style>

<script>
export default {
  name: 'EventCreate',
  data: () => ({
    event_loading: false,
    name: '',
    description: '',
  }),
  methods: {
    create_event() {
      this.event_loading = true;
      const self = this;
      this.post('/api/events/create', {
        name: this.name,
        description: this.description,
      }).then((resp) => {
        if (resp.success) {
          self.$store.dispatch('get_events');
          self.$store.commit('open_snackbar', 'Created event successfully!');
          self.$router.push({ name: 'home' });
        } else {
          self.$store.commit('open_snackbar', 'Failed to create event.');
        }
      }).catch(() => {
        self.$store.commit('open_snackbar', 'Network error while creating event.');
      });
    },
  },
};
</script>
