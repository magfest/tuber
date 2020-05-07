<template>
  <div>
    <v-card max-width="1000" :raised="true" class="mx-auto">
        <v-card-title>Room Night Approvals</v-card-title>
        <v-card-text>
          <p>This page lists each department for which you are permitted to approve edge night requests.</p>

          <p>This year, the available nights are:
          <ul>
            <li v-for="night in room_nights" :key="night.id">{{ night.name + (night.restricted ? " ("+ night.restriction_type +")" : "") }}</li>
          </ul></p>

          <p>For each night, you may either approve (<v-icon>check</v-icon>), deny (<v-icon>clear</v-icon>), or ignore (<v-icon>check_box_outline_blank</v-icon>)
          the request by clicking on the room night itself.</p>
          <p>A night is considered approved if <b>any</b> of a staffer's department heads approve it. This means you should only worry about approving staffers for
          nights you know you will need for your department.</p>
          <p>Denying a room night does not prevent a staffer from getting a room for that night if they are accepted
          by another department, this only serves as a note to you and other department heads of your department.</p>
        </v-card-text>
    </v-card>
    <div v-for="department in departments" :key="department.id">
      <br>
      <v-card max-width="1000" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>{{ department.name }}</v-card-title>
        <v-card-text>
          <v-data-table :headers="headers" :items="department.requests">
            <template v-slot:item.room_nights="{ item }">
              <div v-for="night in room_nights" :key="night.id">
                <v-chip small style="cursor: pointer" v-if="night.restricted && Object.prototype.hasOwnProperty.call(item.room_nights, night.id.toString()) && item.room_nights[night.id.toString()].requested" @click="approve(item.room_nights[night.id.toString()], department.id)">
                  <v-icon left>{{ item.room_nights[night.id.toString()].approved ? "check" : item.room_nights[night.id.toString()].approved===false ? "clear" : "check_box_outline_blank" }}</v-icon>
                  {{ night.name }}
                </v-chip>
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
            <template v-slot:item.approve="{ item }">
              <v-icon style="cursor: pointer" @click="approve_all(item, department.id)">check</v-icon>
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
      {
        text: 'Approve All',
        value: 'approve',
        align: 'right',
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
          }).catch(() => {
            self.notify('Failed to load hotel request.');
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
          }).catch(() => {
            self.notify('Failed to load room nights.');
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
          self.notify(`Could not approve room night: ${res.reason}`);
        }
      }).catch(() => {
        self.notify('Failed to approve room night.');
      });
    },
    approve_all(person, department) {
      let assigned = false;
      let approved = true;
      for (let i = 0; i < this.room_nights.length; i += 1) {
        if (!assigned) {
          if (this.room_nights[i].restricted && Object.prototype.hasOwnProperty.call(person.room_nights, this.room_nights[i].id.toString()) && person.room_nights[this.room_nights[i].id.toString()].requested) {
            ({ approved } = person.room_nights[this.room_nights[i].id.toString()]);
            assigned = true;
          }
        } else if (this.room_nights[i].restricted && Object.prototype.hasOwnProperty.call(person.room_nights, this.room_nights[i].id.toString()) && person.room_nights[this.room_nights[i].id.toString()].requested) {
          person.room_nights[this.room_nights[i].id.toString()].approved = approved;
        }
      }
      for (let i = 0; i < this.room_nights.length; i += 1) {
        if (this.room_nights[i].restricted && Object.prototype.hasOwnProperty.call(person.room_nights, this.room_nights[i].id.toString()) && person.room_nights[this.room_nights[i].id.toString()].requested) {
          this.approve(person.room_nights[this.room_nights[i].id.toString()], department);
        }
      }
    },
  },
};
</script>
