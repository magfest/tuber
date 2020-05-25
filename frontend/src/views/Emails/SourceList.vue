<template>
  <div>
      <br>
      <v-dialog v-model="edit_modal_active" max-width="1200">
        <email-source-form v-model="email_source" @input="edit_modal_active = false" @saved="$asyncComputed.email_sources.update()"></email-source-form>
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
          <v-btn @click="edit_email_source(Object.assign({}, default_email_source))">Add</v-btn>
        </v-card-text>
      </v-card>
    </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';
import EmailSourceForm from './SourceForm.vue';
import { mapAsyncDump } from '../../mixins/rest';

export default {
  name: 'EmailSourceList',
  components: {
    EmailSourceForm,
  },
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
      active: false,
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
      this.email_source = { ...emailSource };
      this.edit_modal_active = true;
    },
  },
};
</script>
