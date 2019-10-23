<template>
  <div>
    <div v-for="department in departments" :key="department.id">
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>{{ department.name }}</v-card-title>
        <v-card-text>
          <v-data-table :headers="headers" :items="department.requests">
            <template v-slot:item.room_nights="{ item }">
              <div v-for="night in room_nights" :key="night.id">
                <div style="cursor: pointer" v-if="night.restricted && Object.prototype.hasOwnProperty.call(item.room_nights, night.id.toString()) && item.room_nights[night.id.toString()].requested" @click="approve(item.room_nights[night.id.toString()], department.id)">
                  <v-icon>{{ item.room_nights[night.id.toString()].approved ? "check" : item.room_nights[night.id.toString()].approved===false ? "clear" : "check_box_outline_blank" }}</v-icon>
                  {{ night.name }}
                </div>
              </div>
            </template>
            <template v-slot:item.name="{ item }">
              <div v-if="checkPermission('hotel_assignment.read')">
                <router-link :to="{name: 'hotelsrequestview', params: {badge: item.id}}">
                  {{ item.name }}
                </router-link>
              </div>
              <div v-else>
                {{ item.name }}
              </div>
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
  name: 'RequestApprove',
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
        text: 'Nights',
        value: 'room_nights',
      },
      {
        text: 'Justification',
        value: 'justification',
      },
    ],
  }),
  computed: {
    ...mapGetters([
      'event',
      'user',
    ]),
  },
  asyncComputed: {
    departments() {
      const self = this;
      return new Promise((resolve) => {
        if (self.event.id && self.user.id) {
          self.get('/api/hotels/requests', {
            event: self.event.id,
            user: self.user.id,
          }).then((depts) => {
            if (depts.success) {
              resolve(depts.departments);
            } else {
              resolve([]);
            }
          });
        } else {
          resolve([]);
        }
      });
    },
    room_nights() {
      const self = this;
      return new Promise((resolve) => {
        if (self.event.id) {
          self.get('/api/hotels/room_nights', {
            event: self.event.id,
          }).then((res) => {
            if (res.success) {
              resolve(res.room_nights);
            } else {
              resolve([]);
            }
          });
        } else {
          resolve([]);
        }
      });
    },
  },
  mounted() {
  },
  methods: {
    approve(request, department) {
      const self = this;
      if (request.approved === true) {
        request.approved = false;
      } else if (request.approved === false) {
        request.approved = null;
      } else {
        request.approved = true;
      }
      self.post('/api/hotels/approve', {
        event: self.event.id,
        room_night_request: request.id,
        department,
        approved: request.approved,
      }).then((res) => {
        if (!res.success) {
          self.$store.commit('open_snackbar', `Could not approve room night: ${res.reason}`);
        }
      });
    },
  },
};
</script>
