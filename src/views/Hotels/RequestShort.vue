<template>
  <div>
    <div v-if="request">
      <router-link v-if="badge" :to="{name: 'hotelsrequestview', params: {badge: badge_id}}">
        View full request for {{ badge.first_name }} {{ badge.last_name }}
      </router-link><br><br>
      <v-checkbox dense class="my-n5" v-model="request.decline" label="Declined Hotel Space"></v-checkbox><br>

      <v-checkbox dense class="my-n5" v-for="night in request.room_nights" v-model="night.checked" :key="night.name" :label="night.restricted ? night.name + ' (' + night.restriction_type + ')' : night.name" :disabled="request.decline">
      </v-checkbox><br>

      <v-textarea label="Justification" v-model="request.justification" @input="blah" counter="200" v-if="justification_required" :disabled="request.decline" outlined placeholder="justification"></v-textarea>

      <roommate-field label="Requested Roommates" v-model="request.requested_roommates" :disabled="request.decline"></roommate-field><br>

      <roommate-field label="Anti-requested Roommates" v-model="request.antirequested_roommates" :disabled="request.decline"></roommate-field><br>

      <v-textarea label="Notes" v-model="request.notes" counter="512" :disabled="request.decline" outlined placeholder="notes"></v-textarea>
    </div>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';
import RoommateField from './RoommateField.vue';

export default {
  name: 'request-short',
  components: {
    RoommateField,
  },
  data: () => ({
    loading: false,
    confirmation: false,
    noise_levels: [
      'Quiet - I am quiet, and prefer quiet.',
      "Moderate - I don't make a lot of noise.",
      "Loud - I'm ok if someone snores or I snore.",
    ],
    sleep_times: [
      '8pm-10pm',
      '10pm-12am',
      '12am-2am',
      '2am-4am',
      '4am-6am',
      '6am-8am',
      '8am-10am',
      '10am-12pm',
      '12pm-2pm',
      '2pm-4pm',
      '4pm-6pm',
      '6pm-8pm',
      'I have no idea.',
    ],
  }),
  props: {
    badge_id: Number,
  },
  computed: {
    ...mapGetters([
      'logged_in',
      'event',
      'user',
    ]),
    justification_required() {
      if (!this.request.room_nights) {
        return false;
      }
      for (let i = 0; i < this.request.room_nights.length; i += 1) {
        if (this.request.room_nights[i].restricted && this.request.room_nights[i].checked) {
          return true;
        }
      }
      return false;
    },
  },
  asyncComputed: {
    departments() {
      const self = this;
      return new Promise((resolve) => {
        if (self.event.id) {
          self.post('/api/hotels/department_membership', {
            event: self.event.id,
            user: self.user.id,
          }).then((depts) => {
            if (depts.success) {
              resolve(depts.departments);
            } else {
              resolve([]);
            }
          }).catch(() => {
            self.$store.commit('open_snackbar', 'Failed to retrieve department membership.');
          });
        } else {
          resolve([]);
        }
      });
    },
    request() {
      const self = this;
      return new Promise((resolve, reject) => {
        if (self.badge) {
          self.get('/api/hotels/request', {
            badge: self.badge.id,
          }).then((res) => {
            if (res.success) {
              resolve(res.request);
            } else {
              reject(Error('Failed to retrieve request'));
            }
          }).catch(() => {
            self.$store.commit('open_snackbar', 'Failed to fetch your request.');
          });
        } else {
          resolve({});
        }
      });
    },
    badge() {
      const self = this;
      return new Promise((resolve) => {
        self.post('/api/user/badge', { badge: self.badge_id }).then((res) => {
          if (res.success) {
            resolve(res.badge);
          } else {
            resolve(null);
          }
        }).catch(() => {
          self.$store.commit('open_snackbar', 'Failed to retrieve badge.');
        });
      });
    },
  },
  mounted() {
  },
  methods: {
    blah() {
      const len = this.request.justification.length;
      const max = 200;
      if (len > max) {
        this.request.justification = this.request.justification.slice(0, max);
        this.request.justification += 'blah '.repeat(Math.floor((len - max) / 5));
        if (this.request.justification.length < len) {
          this.request.justification += 'blah '.slice(0, (len % 5));
        }
      }
    },
    save() {
      const self = this;
      return new Promise((resolve) => {
        self.post('/api/hotels/request', {
          badge: self.badge.id,
          request: self.request,
        }).then((res) => {
          if (res.success) {
            resolve(true);
          } else {
            resolve(false);
          }
        }).catch(() => {
          resolve(false);
        });
      });
    },
  },
  watch: {
  },
};
</script>
