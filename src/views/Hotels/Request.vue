<template>
  <div>
    <div>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Staff Hotel Room Request Form</v-card-title>
        <v-card-text>
          <v-form>
            <p>These questions will help us find the best roommates for you. If you already have a group you'd like to room with the best way to be grouped
              together is to each request each other as roommates, and request the same nights. If this is your first time in staff housing or you don't
              know who you would like to room with then this form will help us match you with compatible roommates.</p>

            <p class="accent--text">Rooms are best-effort, we take your request details into consideration, but cannot guarantee assignments will perfectly match requests.</p><br>

            <p class="font-weight-black">Let us know if you don't want to apply for a room:</p>
            <v-checkbox class="my-n5" v-model="decline" label="I do NOT want a staff room."></v-checkbox><br>

            <p class="font-weight-black">Which nights would you like a room?</p>
            <p>Nights marked "Setup" or "Teardown" will require department head approval. Talk to your department head for details.</p>
            <v-checkbox class="my-n5" v-for="night in room_nights" v-model="night.checked" :key="night.name" :label="night.name" :disabled="decline">
            </v-checkbox><br>

            <p class="font-weight-black">Who would you like to room with?</p>
            <roommate-field label="Requested Roommates" v-model="requested_roommates" :disabled="decline"></roommate-field><br>

            <p class="font-weight-black">Who would you <b>not</b> like to room with?</p>
            <roommate-field label="Anti-requested Roommates" v-model="antirequested_roommates" :disabled="decline"></roommate-field><br>

            <p class="font-weight-black">Is there anything else we should know?</p>
            <v-textarea v-model="notes" :disabled="decline" outlined placeholder="I'm allergic to down pillows/I need to be able to take the stairs to my room/I like the view from the 19th floor and I see elevators as a challenge"></v-textarea>

            <v-divider></v-divider><br>
            <p class="accent--text">The following questions are optional, but will help us match you with roommates.
              Note that the above roommate requests and anti-requests will take precedence over the below preferences.</p><br>

            <p class="font-weight-black">Would you prefer to room with other people in your department?</p>
            <v-checkbox class="my-n5" :disabled="decline" v-model="prefer_department" label="Yes, I would prefer to room with my department."></v-checkbox>
            <p v-if="prefer_department && departments.length > 1">You are assigned to multiple departments. Select your preferred department to room with:</p>
            <v-select :disabled="decline" :items="departments" v-if="prefer_department && departments.length > 1" item-text="name" item-value="id" v-model="preferred_department"></v-select>
            <p v-if="prefer_department && departments.length == 1">We will try to put you with the {{ departments[0].name }} department.</p><br>

            <p class="font-weight-black">Would you prefer single gender rooming?</p>
            <v-checkbox class="my-n5" :disabled="decline" v-model="single_gender" label="Yes, I would prefer a single-gender room."></v-checkbox>
            <p v-if="single_gender">What gender would you like to room with?</p>
            <v-text-field :disabled="decline" v-if="single_gender" v-model="gender" hint="We will do our best to group entries logically. I.E. males will be grouped with guys." label="Gender"></v-text-field><br>

            <p class="font-weight-black">What is your preferred noise level?</p>
            <v-select :disabled="decline" v-model="noise_level" :items="noise_levels"></v-select><br>

            <p class="font-weight-black">Are you sensitive to smoke?</p>
            <v-checkbox class="my-n5" :disabled="decline" v-model="smoke_sensitive" label="I am sensitive to smoke."></v-checkbox><br>

            <p class="font-weight-black">When do you plan to go to sleep?</p>
            <v-select :disabled="decline" v-model="sleep_time" :items="sleep_times"></v-select><br>

            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn outlined type="submit" @click="submitRequest">Submit</v-btn>
            </v-card-actions>
          </v-form>
        </v-card-text>
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
    decline: false,
    loading: false,
    requested_roommates: [],
    antirequested_roommates: [],
    prefer_department: false,
    preferred_department: null,
    notes: '',
    single_gender: false,
    gender: '',
    noise_levels: [
      'Quiet - I am quiet, and prefer quiet.',
      "Moderate - I don't make a lot of noise.",
      "Loud - I'm ok if someone snores or I snore.",
    ],
    noise_level: "Moderate - I don't make a lot of noise.",
    smoke_sensitive: false,
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
    ],
    sleep_time: '12am-2am',
    departments: [
      {
        name: 'TechOps',
        id: 0,
      },
      {
        name: 'Swadges',
        id: 1,
      },
    ],
    room_nights: [
      {
        name: 'Monday (Setup)',
        checked: false,
      },
      {
        name: 'Tuesday (Setup)',
        checked: false,
      },
      {
        name: 'Wednesday (Setup)',
        checked: false,
      },
      {
        name: 'Thursday',
        checked: true,
      },
      {
        name: 'Friday',
        checked: true,
      },
      {
        name: 'Saturday',
        checked: true,
      },
      {
        name: 'Sunday (Teardown)',
        checked: false,
      },
      {
        name: 'Monday (Teardown)',
        checked: false,
      },
    ],
  }),
  computed: {
    ...mapGetters([
      'logged_in',
    ]),
  },
  mounted() {
    const self = this;
    if (!this.logged_in) {
      this.post('/api/hotels/staffer_auth', {
        token: this.$route.query.id,
      }).then((resp) => {
        if (resp.success) {
          self.$store.dispatch('check_logged_in').then(() => {
            self.$store.dispatch('get_events');
            self.$store.commit('open_snackbar', 'Login Successful');
          });
        } else {
          self.$store.commit('open_snackbar', 'Failed to authenticate. Please contact STOPS for help.');
        }
      }).catch(() => {
        self.$store.commit('open_snackbar', 'Network error while logging in.');
      });
    }
  },
  methods: {
    submitRequest() {

    },
  },
};
</script>
