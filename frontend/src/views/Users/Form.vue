<template>
     <v-card :loading="loading">
        <v-card-title class="headline grey lighten-2" primary-title>
            Edit User
        </v-card-title>
        <br>
        <v-card-text>
            <v-form>
                <v-text-field label="Username" v-model="value.username"></v-text-field>
                <v-text-field label="Email" v-model="value.email"></v-text-field>
                <v-checkbox label="Active" v-model="value.active"></v-checkbox>
                <v-text-field label="Password" v-model="password" type="password"></v-text-field>
                <v-text-field label="Confirm Password" v-model="confirm_password" type="password"></v-text-field>
            </v-form>
            <h3>Roles</h3>
            <v-data-table item-key="id" :headers="headers" :items="user_roles">
                <template v-slot:item.event="{ item }">
                    <v-select v-model="item.event" :items="events" item-text="name" item-value="id"></v-select>
                </template>
                <template v-slot:item.department="{ item }">
                    <v-select v-model="item.department" :items="departments[item.event]" item-text="name" item-value="id"></v-select>
                </template>
            </v-data-table>
            <v-btn>Add Role</v-btn>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn left @click="$emit('input')">Close</v-btn>
            <v-btn color="primary" text @click="save_data">Save</v-btn>
        </v-card-actions>
    </v-card>
</template>

<script>
import { mapAsyncObjects } from '../../mixins/rest';

export default {
  name: 'user-form',
  components: {
  },
  data: () => ({
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
        text: 'Event',
        value: 'event',
      },
      {
        text: 'Department',
        value: 'department',
      },
    ],
  }),
  props: {
    value: {
      default: () => ({
        username: '',
        email: '',
        active: false,
        password: '',
        confirm_password: '',
      }),
    },
  },
  computed: {
    user_roles() {
      const grantedRoles = [];
      for (let i = 0; i < this.value.grants.length; i += 1) {
        grantedRoles.push(this.roles[this.grants[this.value.grants[i]].role]);
      }
      return grantedRoles;
    },
  },
  asyncComputed: {
    ...mapAsyncObjects([
      'departments',
      'roles',
      'events',
      'grants',
    ]),
  },
  methods: {
    save_data() {
      this.loading = true;
      this.save('users', this.value).then(() => {
        if (this.password) {
          if (!(this.password.length >= 8)) {
            this.notify('Password must be at least 8 characters long.');
            return;
          }
          if (this.password !== this.confirm_password) {
            this.notify('Password confirmation does not match.');
            return;
          }
          this.post('/api/change_password', { password: this.password }).then(() => {
            this.notify('User and password saved successfully.');
            this.loading = false;
            this.password = '';
            this.confirm_password = '';
            this.$emit('saved');
            this.$emit('input');
          }).catch(() => {
            this.notify('Failed to save password.');
            this.loading = false;
          });
        } else {
          this.notify('User saved successfully.');
          this.loading = false;
          this.$emit('saved');
          this.$emit('input');
        }
      }).catch(() => {
        this.loading = false;
        this.notify('Failed to save user.');
      });
    },
  },
};
</script>
