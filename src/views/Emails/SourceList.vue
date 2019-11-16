<template>
  <div>
      <br>
      <v-dialog v-model="add_modal" width="500">
        <v-card :loading="loading">
          <v-card-title class="headline grey lighten-2" primary-title>Edit Email Source</v-card-title>

          <v-card-text>
            <v-form>
              <v-text-field label="Name" v-model="name"></v-text-field>
              <v-text-field label="Description" v-model="description"></v-text-field>
              <v-text-field label="From Address" v-model="address"></v-text-field>
              <v-text-field label="SES Access Key" v-model="ses_access_key"></v-text-field>
              <v-text-field label="SES Secret Key" v-model="ses_secret_key"></v-text-field>
              <v-text-field label="AWS Region" v-model="region"></v-text-field>
            </v-form>
          </v-card-text>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn left @click="add_modal = false">Close</v-btn>
            <v-btn color="primary" text @click="add_email_source">Save</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Email Sources</v-card-title>
        <v-card-text>
          <v-data-table :headers="headers" :items="sources"></v-data-table>
          <v-btn @click="add_modal = true">Add</v-btn>
        </v-card-text>
      </v-card>
    </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'EmailSourceList',
  data: () => ({
    loading: false,
    add_modal: false,
    name: '',
    description: '',
    address: '',
    ses_access_key: '',
    ses_secret_key: '',
    region: '',
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
    sources: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          if (self.event.id) {
            self.get('/api/emails/sources', { event: self.event.id }).then((res) => {
              if (res.success) {
                resolve(res.sources);
              } else {
                resolve(res.sources);
              }
            }).catch(() => {
              self.$store.commit('open_snackbar', 'Failed to load existing email sources.');
            });
          }
        });
      },
      default: [],
    },
  },
  methods: {
    add_email_source() {
      this.loading = true;
      const self = this;
      self.post('/api/emails/sources', {
        event: self.event.id,
        name: self.name,
        description: self.description,
        address: self.address,
        ses_access_key: self.ses_access_key,
        ses_secret_key: self.ses_secret_key,
        region: self.region,
      }).then((res) => {
        self.loading = false;
        if (res.success) {
          self.add_modal = false;
          self.name = '';
          self.description = '';
          self.address = '';
          self.ses_access_key = '';
          self.ses_secret_key = '';
          self.region = '';
          self.$asyncComputed.sources.update();
          self.$store.commit('open_snackbar', 'Added email source successfully.');
        } else {
          self.$store.commit('open_snackbar', res.reason);
        }
      }).catch(() => {
        self.$store.commit('open_snackbar', 'Failed to update email source.');
        self.loading = false;
      });
    },
  },
};
</script>
