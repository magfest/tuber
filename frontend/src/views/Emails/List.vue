<template>
  <div>
      <br>
      <v-dialog v-model="edit_modal_active" max-width="1200">
        <email-form v-model="email" @input="edit_modal_active=false" @saved="$asyncComputed.emails.update()"></email-form>
      </v-dialog>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Emails</v-card-title>
        <v-card-text>
          <v-data-table :headers="headers" :items="emails">
            <template v-slot:item.active="{ item }">
              <v-icon>{{ item.active ? "check" : "check_box_outline_blank" }}</v-icon>
            </template>
            <template v-slot:item.name="{ item }">
              <div @click="edit_email(item)" style="cursor: pointer; color: blue">{{ item.name }}</div>
            </template>
            <template v-slot:item.delete="{ item }">
              <v-icon style="cursor: pointer" @click="delete_email(item)">delete</v-icon>
            </template>
            <template v-slot:item.trigger="{ item }">
              <v-icon style="cursor: pointer" @click="trigger_email(item)">email</v-icon>
            </template>
            <template v-slot:item.download="{ item }">
              <a :href="'/api/emails/csv?event='+event.id+'&email='+item.id+'&csrf_token='+$cookies.get('csrf_token')"><v-icon>cloud_download</v-icon></a>
            </template>
          </v-data-table>
          <v-btn @click="edit_email(Object.assign({}, default_email))">Add</v-btn>
        </v-card-text>
      </v-card>
    </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';
import EmailForm from './Form.vue';
import { mapAsyncDump } from '../../mixins/rest';

export default {
  name: 'EmailList',
  components: {
    EmailForm,
  },
  data: () => ({
    loading: false,
    edit_modal_active: false,
    email: {},
    default_email: {
      name: 'New Email',
      description: '',
      code: 'return function(context)\n   -- This function gets called on every potential email-generating event.\n   -- If it returns true then the email will be sent.\n   -- context is an object that contains the referenced event, and badge.\n  return true\nend',
      subject: '',
      body: '',
      active: false,
      send_once: true,
      source: 1,
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
        text: 'Active',
        value: 'active',
      },
      {
        text: 'Delete',
        value: 'delete',
      },
      {
        text: 'Manual Trigger',
        value: 'trigger',
      },
      {
        text: 'Download',
        value: 'download',
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
      'emails',
    ]),
  },
  methods: {
    trigger_email(email) {
      const self = this;
      self.loading = true;
      self.post('/api/emails/trigger', {
        email: email.id,
        event: self.event.id,
      }).then(() => {
        self.loading = false;
        self.notify('Email triggered successfully.');
      }).catch(() => {
        self.loading = false;
        self.notify('Failed to trigger email.');
      });
    },
    delete_email(email) {
      this.loading = true;
      this.remove('emails', email).then(() => {
        this.loading = false;
        this.notify(`Email ${email.name} deleted successfully.`);
      }).catch(() => {
        this.loading = false;
        this.notify(`Failed to delete email ${email.name}`);
      });
    },
    edit_email(email) {
      this.email = email;
      this.edit_modal_active = true;
    },
  },
};
</script>
