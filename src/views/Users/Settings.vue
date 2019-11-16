<template>
  <div>
    <div>
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Users</v-card-title>
        <v-card-text>
            <v-data-table item-key="id" :headers="headers" :items="users">
                <template v-slot:item.active="{ item }">
                    <v-icon>
                        {{ item.active ? "check_box" : "check_box_outline_blank" }}
                    </v-icon>
                </template>
                <template v-slot:item.username="{ item }">
                    <router-link :to="{ name: 'useredit', params: { id: item.id }}">{{ item.username }}</router-link>
                </template>
            </v-data-table>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'UserSettings',
  components: {
  },
  data: () => ({
    loading: false,
    selected: [],
    headers: [
      {
        text: 'Username',
        value: 'username',
      },
      {
        text: 'Email',
        value: 'email',
        align: 'center',
      },
      {
        text: 'Active',
        value: 'active',
      },
    ],
  }),
  computed: {
    ...mapGetters([
    ]),
  },
  asyncComputed: {
    users: {
      get() {
        const self = this;
        return new Promise((resolve) => {
          self.get('/api/users').then((res) => {
            if (res.success) {
              resolve(res.users);
            }
            resolve(res.users);
          }).catch(() => {
            self.$store.commit('open_snackbar', 'Failed to retrieve users');
            resolve([]);
          });
        });
      },
      default: [],
    },
  },
  mounted() {
  },
  methods: {
  },
};
</script>
