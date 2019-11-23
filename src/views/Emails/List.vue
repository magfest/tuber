<template>
  <div>
      <br>
      <v-dialog v-model="edit_modal_active" max-width="1200">
        <v-card :loading="loading">
          <v-card-title class="headline grey lighten-2" primary-title>Create New Email</v-card-title>

          <v-card-text>
            <br>
            <v-form>
              <v-text-field outlined label="Name" v-model="email.name"></v-text-field>
              <v-text-field outlined label="Description" v-model="email.description"></v-text-field>
              <p>Send filter (lua)</p>
              <editor v-model="email.code" lang="lua" width="650" height="200"></editor><br>
              <v-text-field outlined label="Subject" v-model="email.subject"></v-text-field>
              <v-textarea outlined label="Body" v-model="email.body"></v-textarea>
              <v-checkbox outlined v-model="email.active" label="Active"></v-checkbox>
              <v-checkbox outlined v-model="email.send_once" label="Only send once"></v-checkbox>
              <v-select outlined label="Email Source" v-model="email.source" :items="sources" item-text="display" item-value="id"></v-select>
            </v-form>
          </v-card-text>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn left @click="edit_modal_active = false">Close</v-btn>
            <v-btn color="primary" text @click="save_email">Save</v-btn>
          </v-card-actions>
        </v-card>
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
          <v-btn @click="edit_email(default_email)">Add</v-btn>
        </v-card-text>
      </v-card>
    </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';
import editor from 'vue2-ace-editor';
import { mapAsyncDump } from '../../mixins/rest';
import 'brace/ext/language_tools';
import 'brace/mode/lua';
import 'brace/theme/chrome';

export default {
  name: 'EmailList',
  components: {
    editor,
  },
  data: () => ({
    loading: false,
    edit_modal_active: false,
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
    email: {},
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
    sources() {
      const result = [];
      this.email_sources.forEach((emailSource) => {
        emailSource.display = `${emailSource.address} (${emailSource.name})`;
        result.push(emailSource);
      });
      return result;
    },
  },
  asyncComputed: {
    ...mapAsyncDump([
      'emails',
      'email_sources',
    ]),
  },
  methods: {
    trigger_email(email) {
      const self = this;
      self.loading = true;
      self.post('/api/emails/trigger', {
        email: email.id,
        event: self.event.id,
      }).then((res) => {
        self.loading = false;
        if (res.success) {
          self.$store.commit('open_snackbar', 'Email triggered successfully.');
        } else {
          self.$store.commit('open_snackbar', res.reason);
        }
      }).catch(() => {
        self.loading = false;
        self.$store.commit('open_snackbar', 'Failed to trigger email.');
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
      this.email = Object.assign({}, email);
      this.edit_modal_active = true;
    },
    save_email() {
      this.loading = true;
      this.save('emails', this.email).then(() => {
        this.loading = false;
        this.email = {};
        this.edit_modal_active = false;
      }).catch(() => {
        this.loading = false;
        this.notify('Failed to add email.');
      });
    },
  },
};
</script>
