<template>
  <div>
      <br>
      <v-dialog v-model="edit_modal_active" width="500">
        <v-card :loading="loading">
          <v-card-title class="headline grey lighten-2" primary-title>Edit Email Source</v-card-title>

          <v-card-text>
            <v-form>
              <v-text-field label="Name" v-model="email_source.name"></v-text-field>
              <v-text-field label="Description" v-model="email_source.description"></v-text-field>
              <v-text-field label="From Address" v-model="email_source.address"></v-text-field>
              <v-text-field label="SES Access Key" v-model="email_source.ses_access_key"></v-text-field>
              <v-text-field label="SES Secret Key" v-model="email_source.ses_secret_key"></v-text-field>
              <v-text-field label="AWS Region" v-model="email_source.region"></v-text-field>
              <v-checkbox label="Active" v-model="email_source.active"></v-checkbox>
            </v-form>
          </v-card-text>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn left @click="edit_modal_active = false">Close</v-btn>
            <v-btn color="primary" text @click="save_email_source">Save</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Email Sources</v-card-title>
        <v-card-text>
          <v-data-table :headers="headers" :items="email_sources">
            <template v-slot:item.active="{ item }">
              <v-icon>{{ item.active ? "check" : "check_box_outline_blank" }}</v-icon>
            </template>
            <template v-slot:item.name="{ item }">
              <div @click="edit_email_source(item)" style="cursor: pointer; color: blue">{{ item.name }}</div>
            </template>
            <template v-slot:item.delete="{ item }">
              <v-icon style="cursor: pointer" @click="delete_email_source(item)">delete</v-icon>
            </template>
          </v-data-table>
          <v-btn @click="edit_email_source(default_email_source)">Add</v-btn>
        </v-card-text>
      </v-card>
    </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';
import { mapAsyncDump } from '../../mixins/rest';

export default {
  name: 'EmailSourceList',
  data: () => ({
    loading: false,
    edit_modal_active: false,
    default_email_source: {
      name: 'New Email Source',
      description: '',
      address: '',
      ses_access_key: '',
      ses_secret_key: '',
      region: '',
      active: true,
    },
    email_source: {},
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
      {
        text: 'Delete',
        value: 'delete',
      },
      {
        text: 'Active',
        value: 'active',
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
      'email_sources',
    ]),
  },
  methods: {
    delete_email_source(emailSource) {
      this.loading = true;
      this.remove('email_sources', emailSource).then(() => {
        this.loading = false;
        this.notify(`Email Source ${emailSource.name} deleted successfully.`);
      }).catch(() => {
        this.loading = false;
        this.notify(`Failed to delete email source ${emailSource.name}`);
      });
    },
    edit_email_source(emailSource) {
      this.email_source = Object.assign({}, emailSource);
      this.edit_modal_active = true;
    },
    save_email_source() {
      this.loading = true;
      this.save('email_sources', this.email_source).then(() => {
        this.loading = false;
        this.email_source = {};
        this.edit_modal_active = false;
      }).catch(() => {
        this.loading = false;
        this.notify('Failed to add email.');
      });
    },
  },
};
</script>
