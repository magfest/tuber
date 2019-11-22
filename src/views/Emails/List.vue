<template>
  <div>
      <br>
      <v-dialog v-model="add_modal" max-width="1200">
        <v-card :loading="loading">
          <v-card-title class="headline grey lighten-2" primary-title>Create New Email</v-card-title>

          <v-card-text>
            <br>
            <v-form>
              <v-text-field outlined label="Name" v-model="name"></v-text-field>
              <v-text-field outlined label="Description" v-model="description"></v-text-field>
              <p>Send filter (lua)</p>
              <editor v-model="code" lang="lua" width="650" height="200"></editor><br>
              <v-text-field outlined label="Subject" v-model="subject"></v-text-field>
              <v-textarea outlined label="Body" v-model="body"></v-textarea>
              <v-checkbox outlined v-model="active" label="Active"></v-checkbox>
              <v-checkbox outlined v-model="send_once" label="Only send once"></v-checkbox>
              <v-select outlined label="Email Source" v-model="source" :items="sources" item-text="display" item-value="id"></v-select>
            </v-form>
          </v-card-text>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn left @click="add_modal = false">Close</v-btn>
            <v-btn color="primary" text @click="add_email">Save</v-btn>
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
          <v-btn @click="add_modal = true">Add</v-btn>
        </v-card-text>
      </v-card>
    </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';
import editor from 'vue2-ace-editor';
import 'brace/ext/language_tools';
import 'brace/mode/lua';
import 'brace/theme/chrome';

export default {
  name: 'EmailList',
  components: {
    editor,
  },
  data: () => ({
    default_code: 'return function(context)\n   -- This function gets called on every potential email-generating event.\n   -- If it returns true then the email will be sent.\n   -- context is an object that contains the referenced event, and badge.\n  return true\nend',
    loading: false,
    add_modal: false,
    id: null,
    name: '',
    description: '',
    code: '',
    subject: '',
    body: '',
    active: false,
    source: null,
    send_once: false,
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
    emails: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          if (self.event.id) {
            self.get('/api/emails', { event: self.event.id }).then((res) => {
              if (res.success) {
                resolve(res.emails);
              } else {
                resolve(res.emails);
              }
            }).catch(() => {
              self.$store.commit('open_snackbar', 'Failed to retrieve emails.');
            });
          }
        });
      },
      default: [],
    },
    sources: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          if (self.event.id) {
            self.get('/api/emails/sources', { event: self.event.id }).then((res) => {
              if (res.success) {
                res.sources.forEach((source) => {
                  source.display = `${source.address} (${source.name})`;
                });
                resolve(res.sources);
              } else {
                resolve(res.sources);
              }
            }).catch(() => {
              self.$store.commit('open_snackbar', 'Failed to load available email sources.');
            });
          }
        });
      },
      default: [],
    },
  },
  mounted() {
    this.code = this.default_code;
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
      const self = this;
      self.loading = true;
      self.post('/api/emails/delete', {
        id: email.id,
        event: self.event.id,
      }).then((res) => {
        self.loading = false;
        if (res.success) {
          self.$asyncComputed.emails.update();
          self.$store.commit('open_snackbar', 'Email deleted successfully.');
        } else {
          self.$store.commit('open_snackbar', res.reason);
        }
      }).catch(() => {
        self.loading = false;
        self.$store.commit('open_snackbar', 'Failed to delete email.');
      });
    },
    edit_email(email) {
      this.id = email.id;
      this.name = email.name;
      this.description = email.description;
      this.code = email.code;
      this.subject = email.subject;
      this.body = email.body;
      this.active = email.active;
      this.source = email.source;
      this.send_once = email.send_once;
      this.add_modal = true;
    },
    add_email() {
      this.loading = true;
      const self = this;
      self.post('/api/emails', {
        id: self.id,
        event: self.event.id,
        name: self.name,
        description: self.description,
        code: self.code,
        subject: self.subject,
        body: self.body,
        active: self.active,
        source: self.source,
        send_once: self.send_once,
      }).then((res) => {
        self.loading = false;
        if (res.success) {
          self.id = null;
          self.add_modal = false;
          self.name = '';
          self.description = '';
          self.code = self.default_code;
          self.subject = '';
          self.body = '';
          self.active = false;
          self.source = null;
          self.send_once = false;
          self.$asyncComputed.emails.update();
          self.$store.commit('open_snackbar', 'Added email successfully.');
        } else {
          self.$store.commit('open_snackbar', res.reason);
        }
      }).catch(() => {
        self.loading = false;
        self.$store.commit('open_snackbar', 'Failed to add email.');
      });
    },
  },
};
</script>
