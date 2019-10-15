<template>
  <div>
    <div>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Staff Hotel Request Form</v-card-title>
        <v-card-text>
          <v-form>
            <p>These questions will help us find the best roommates for you. If you already have a group you'd like to room with the best way to be grouped
              together is to each request each other as roommates, and request the same nights. If this is your first time in staff housing or you don't
              know who you would like to room with then this form will help us match you with compatible roommates.</p><br>

            <p>Which nights would you like a room?</p>
            <v-checkbox class="my-n5" v-for="night in room_nights" v-model="night.checked" :key="night.name" :label="night.name">
            </v-checkbox><br>

            <p>Who would you like to room with?</p>
            <roommate-field label="Requested Roommates" v-model="requested_roommates"></roommate-field><br>

            <p>Who would you <b>not</b> like to room with?</p>
            <roommate-field label="Anti-requested Roommates" v-model="antirequested_roommates"></roommate-field><br>

            <p>Would you prefer to room with other people in your department?</p>
            <v-checkbox v-model="prefer_department" label="Prefer my department"></v-checkbox>
            <p v-if="prefer_department && departments.length > 1">You are assigned to multiple departments. Select your preferred department to room with:</p>
            <v-select :items="departments" v-if="prefer_department && departments.length > 1" item-text="name" item-value="id" v-model="preferred_department"></v-select>
            <p v-if="prefer_department && departments.length == 1">We will try to put you with the {{ departments[0].name }} department.</p><br>

            <p>Is there anything else we should know?</p>
            <v-textarea v-model="notes" outlined placeholder="I'm allergic to down pillows/I need to be able to take the stairs to my room/I like the view from the 19th floor and I see elevators as a challenge"></v-textarea>

            <p><b>The following questions are optional, but will help us match you with roommates:</b></p><br>

            <p>Do you prefer single gender rooming?</p>
            <v-checkbox v-model="single_gender" label="I would like to opt-in to single-gendered rooming."></v-checkbox>
            <p v-if="single_gender">What gender would you like to room with?</p>
            <v-text-field v-if="single_gender" v-model="gender" hint="If you identify as an attack helicopter then we will put you in a room with the other attack helicopters." label="Gender"></v-text-field><br>

            <p>What is your preferred noise level? (Do you snore/leave the tv on/otherwise)</p>
            <v-select v-model="noise_level" :items="noise_levels"></v-select><br>

            <p>Are you sensitive to smoke?</p>
            <v-checkbox v-model="smoke_sensitive" label="I am sensitive to smoke."></v-checkbox><br>

            <p>When do you plan to sleep?</p>
            <v-select v-model="sleep_time" :items="sleep_times"></v-select><br>

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
    loading: false,
    requested_roommates: [],
    antirequested_roommates: [],
    prefer_department: false,
    preferred_department: null,
    notes: '',
    single_gender: false,
    gender: '',
    noise_levels: [
      'Quiet',
      'Moderate',
      'Loud',
    ],
    noise_level: 'Quiet',
    smoke_sensitive: false,
    sleep_times: [
      'During the day',
      '8pm',
      '10pm',
      '12am',
      '2am',
    ],
    sleep_time: '',
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
        name: 'Monday',
        checked: false,
      },
      {
        name: 'Tuesday',
        checked: false,
      },
      {
        name: 'Wednesday',
        checked: false,
      },
      {
        name: 'Thursday',
        checked: false,
      },
      {
        name: 'Friday',
        checked: false,
      },
      {
        name: 'Saturday',
        checked: false,
      },
      {
        name: 'Sunday',
        checked: false,
      },
      {
        name: 'Monday',
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
