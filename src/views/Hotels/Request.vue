<template>
  <div>
    <div>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" v-if="badge === null">
        <v-card-title>Staff Hotel Room Request Form</v-card-title>
        <v-card-text>
          <p>Your current user does not have a badge. You must have a badge assigned to request a staff hotel room.</p>
        </v-card-text>
      </v-card>
      <v-card max-width="700" :raised="true" class="mx-auto" v-else-if="!confirmation" :loading="loading || (request === null)">
        <v-card-title>Staff Hotel Room Request Form</v-card-title>
        <v-card-text>
          <p><b>You are filling out this form as {{ badge.first_name }} {{ badge.last_name }}.</b></p>
          <v-form v-if="request !== null">
            <p>These questions will help us find the best roommates for you. If you already have a group you'd like to room with the best way to be grouped
              together is to each request each other as roommates, and request the same nights. If this is your first time in staff housing or you don't
              know who you would like to room with then this form will help us match you with compatible roommates.</p>

            <p class="accent--text">Rooms are best-effort, we take your request details into consideration, but cannot guarantee assignments will perfectly match requests.</p><br>

            <p class="font-weight-black">Let us know if you don't want to apply for a room:</p>
            <v-checkbox class="my-n5" v-model="request.decline" label="I do NOT want a staff room."></v-checkbox><br>

            <p class="font-weight-black">Which nights would you like a room?</p>
            <p>Nights marked "Setup" or "Teardown" will require department head approval. Talk to your department head for details.</p>
            <v-checkbox class="my-n5" v-for="night in request.room_nights" v-model="night.checked" :key="night.name" :label="night.restricted ? night.name + ' (' + night.restriction_type + ')' : night.name" :disabled="request.decline">
            </v-checkbox><br>

            <p class="font-weight-black" v-if="justification_required">Please provide justification for requesting restricted nights:</p>
            <v-textarea v-model="request.justification" counter="512" v-if="justification_required" :disabled="request.decline" outlined placeholder="I'm helping with setup in <department>."></v-textarea>

            <p class="font-weight-black">Who would you like to room with?</p>
            <roommate-field label="Requested Roommates" v-model="request.requested_roommates" :disabled="request.decline"></roommate-field><br>

            <p class="font-weight-black">Who would you <b>not</b> like to room with?</p>
            <roommate-field label="Anti-requested Roommates" v-model="request.antirequested_roommates" :disabled="request.decline"></roommate-field><br>

            <p class="font-weight-black">Is there anything else we should know?</p>
            <v-textarea v-model="request.notes" counter="512" :disabled="request.decline" outlined placeholder="I'm allergic to down pillows/I need to be able to take the stairs to my room/I like the view from the 19th floor and I see elevators as a challenge"></v-textarea>

            <v-divider></v-divider><br>
            <p class="accent--text">The following questions are optional, but will help us match you with roommates.
              Note that the above roommate requests and anti-requests will take precedence over the below preferences.</p><br>

            <p class="font-weight-black">Would you prefer to room with other people in your department?</p>
            <v-checkbox class="my-n5" :disabled="request.decline" v-model="request.prefer_department" label="Yes, I would prefer to room with my department."></v-checkbox>
            <p v-if="request.prefer_department && departments.length > 1">You are assigned to multiple departments. Select your preferred department to room with:</p>
            <v-select :disabled="request.decline" :items="departments" v-if="request.prefer_department && departments.length > 1" item-text="name" item-value="id" v-model="request.preferred_department"></v-select>
            <p v-if="request.prefer_department && departments.length == 1">We will try to put you with the {{ departments[0].name }} department.</p><br>

            <p class="font-weight-black">Would you prefer single gender rooming?</p>
            <v-checkbox class="my-n5" :disabled="request.decline" v-model="request.single_gender" label="Yes, I would prefer a single-gender room."></v-checkbox>
            <p v-if="request.single_gender">What gender would you like to room with?</p>
            <v-text-field :disabled="request.decline" counter="64" v-if="request.single_gender" v-model="request.gender" hint="We will do our best to group entries logically. I.e., males will be grouped with guys." label="Gender"></v-text-field><br>

            <p class="font-weight-black">What is your preferred noise level?</p>
            <v-select :disabled="request.decline" v-model="request.noise_level" :items="noise_levels"></v-select><br>

            <p class="font-weight-black">Would you prefer non-smoking roommates?</p>
            <v-checkbox class="my-n5" :disabled="request.decline" v-model="request.smoke_sensitive" label="Yes, I would prefer non-smoking roommates."></v-checkbox><br>

            <p class="font-weight-black">When do you plan to go to sleep?</p>
            <v-select :disabled="request.decline" v-model="request.sleep_time" :items="sleep_times"></v-select><br>

            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn outlined type="submit" @click="submitRequest">Submit</v-btn>
            </v-card-actions>
          </v-form>
        </v-card-text>
      </v-card>
      <v-card max-width="700" :raised="true" class="mx-auto" v-else :loading="loading || (request === null)">
        <v-card-title>Room Request Confirmation</v-card-title>
        <v-card-text>
          <p>Your room request has been received successfully. You may return to this page at any time until the request deadline to make changes.</p>
        </v-card-text>
        <v-card-actions>
          <v-btn outlined @click="confirmation = false">Go Back</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';
import RoommateField from './RoommateField.vue';

export default {
  name: 'HotelRequest',
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
          });
        } else {
          resolve([]);
        }
      });
    },
    request() {
      const self = this;
      return new Promise((resolve, reject) => {
        console.log('Update request', self.badge);
        if (self.badge) {
          self.get('/api/hotels/request', {
            badge: self.badge.id,
          }).then((res) => {
            if (res.success) {
              resolve(res.request);
            } else {
              reject(Error('Failed to retrieve request'));
            }
          });
        } else {
          resolve({});
        }
      });
    },
    badge() {
      const self = this;
      return new Promise((resolve) => {
        if (self.$route.params.badge) {
          self.post('/api/user/badge', { badge: self.$route.params.badge }).then((res) => {
            if (res.success) {
              resolve(res.badge);
            } else {
              resolve(null);
            }
          });
        } else if (self.event.id && self.user.id) {
          self.post('/api/user/badge', { event: self.event.id, user: self.user.id }).then((res) => {
            if (res.success) {
              resolve(res.badge);
            } else {
              resolve(null);
            }
          });
        }
      });
    },
  },
  mounted() {
  },
  methods: {
    submitRequest() {
      const self = this;
      self.loading = true;
      self.post('/api/hotels/request', {
        badge: self.badge.id,
        request: self.request,
      }).then((res) => {
        if (res.success) {
          self.loading = false;
          self.confirmation = true;
        } else {
          self.loading = false;
          self.$store.commit('open_snackbar', `Failed to submit hotel request: ${res.reason}`);
        }
      });
    },
  },
  watch: {
  },
};
</script>
