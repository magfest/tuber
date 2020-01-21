<template>
  <div>
      <br>
      <v-dialog v-model="edit_modal_active" max-width="1200">
        <user-form v-model="user" @input="edit_modal_active=false" @saved="$asyncComputed.users.update()"></user-form>
      </v-dialog>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Users</v-card-title>
        <v-card-text>
          <v-data-table :headers="headers" :items="users">
            <template v-slot:item.active="{ item }">
              <v-icon>{{ item.active ? "check" : "check_box_outline_blank" }}</v-icon>
            </template>
            <template v-slot:item.username="{ item }">
              <div @click="edit_user(item)" style="cursor: pointer; color: blue">{{ item.username }}</div>
            </template>
            <template v-slot:item.delete="{ item }">
              <v-icon style="cursor: pointer" @click="delete_user(item)">delete</v-icon>
            </template>
          </v-data-table>
          <v-btn @click="edit_user(Object.assign({}, default_user))">Add</v-btn>
        </v-card-text>
      </v-card>
    </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';
import UserForm from './Form.vue';
import { mapAsyncDump } from '../../mixins/rest';

export default {
  name: 'UserList',
  components: {
    UserForm,
  },
  data: () => ({
    loading: false,
    edit_modal_active: false,
    user: {},
    default_user: {
      username: '',
      email: '',
      active: true,
    },
    headers: [
      {
        text: 'Username',
        value: 'username',
      },
      {
        text: 'Email',
        value: 'email',
      },
      {
        text: 'Active',
        value: 'active',
      },
      {
        text: 'Delete',
        value: 'delete',
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
      'users',
    ]),
  },
  methods: {
    delete_user(user) {
      this.loading = true;
      this.remove('users', user).then(() => {
        this.loading = false;
        this.notify(`User ${user.name} deleted successfully.`);
      }).catch(() => {
        this.loading = false;
        this.notify(`Failed to delete user ${user.name}`);
      });
    },
    edit_user(user) {
      this.user = user;
      this.edit_modal_active = true;
    },
  },
};
</script>
