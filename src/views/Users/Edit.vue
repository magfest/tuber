<template>
  <div>
    <div>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Editing {{ user.username }}</v-card-title>
        <v-card-text>
            <v-form>
                <v-text-field label="Username" v-model="user.username"></v-text-field>
                <v-text-field label="Email" v-model="user.email"></v-text-field>
                <v-checkbox label="Active" v-model="user.active"></v-checkbox>
            </v-form>
            <h3>Roles</h3>
            <v-data-table item-key="id" :headers="headers" :items="user.roles">
                <template v-slot:item.event="{ item }">
                    <v-select v-model="item.event" :items="events" item-text="name" item-value="id"></v-select>
                </template>
                <template v-slot:item.department="{ item }">
                    <v-select v-model="item.department" :items="departments[item.event]" item-text="name" item-value="id"></v-select>
                </template>
            </v-data-table>
            <v-btn>Add Role</v-btn>
        </v-card-text>
        <v-card-actions>
            <v-btn color="warning">Delete User</v-btn>
            <v-btn>Save</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'UserEdit',
  components: {
  },
  data: () => ({
    loading: false,
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
  computed: {
    ...mapGetters([
    ]),
  },
  asyncComputed: {
    user: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          self.get('/api/user', { user: self.$route.params.id }).then((res) => {
            if (res.success) {
              resolve(res.user);
            } else {
              resolve({});
            }
          }).catch(() => {
            self.$store.commit('open_snackbar', 'Failed to fetch user.');
          });
        });
      },
      default: {},
    },
    events: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          self.get('/api/events/list').then((res) => {
            if (res.success) {
              res.events.push({ id: null, name: 'All' });
              resolve(res.events);
            } else {
              resolve([]);
            }
          }).catch(() => {
            self.$store.commit('open_snackbar', 'Failed to retrieve list of events.');
          });
        });
      },
      default: [],
    },
    departments: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          self.get('/api/departments/list').then((res) => {
            if (res.success) {
              const keys = Object.keys(res.departments);
              console.log(keys);
              for (let i = 0; i < keys.length; i += 1) {
                res.departments[keys[i]].push({ id: null, name: 'All' });
              }
              res.departments.null = [{ id: null, name: 'All' }];
              console.log(res.departments);
              resolve(res.departments);
            } else {
              resolve({});
            }
          }).catch(() => {
            self.$store.commit('open_snackbar', 'Failed to retrieve list of departments.');
          });
        });
      },
      default: {},
    },
  },
  mounted() {
  },
  methods: {
  },
};
</script>
