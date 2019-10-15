<template>
  <div>
    <div>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Staff Hotel Request Form</v-card-title>
        <v-card-text>
          <v-form>
            <p>Please fill out our standard questionaire:</p>
            <p>Which nights would you like a room?</p>
            <v-checkbox class="my-n5" v-for="night in room_nights" v-model="night.checked" :key="night.name" :label="night.name">
            </v-checkbox>
            <p>Who would you like to room with?</p>
            <roommate-field label="Requested Roommates" v-model="requested_roommates"></roommate-field>
            {{ requested_roommates }}
            <p>Who would you <b>not</b> like to room with?</p>
            <roommate-field label="Anti-requested Roommates" v-model="antirequested_roommates"></roommate-field>
            {{ antirequested_roommates }}
            <!--
              Room Nights:
                Multiple checkboxes based off of the RoomNights model.
                If a room night is checked that is "restricted", pop up a textbox requiring
                  the user to justify why they need that night.
              Roommate Requests:
                None or more input boxes allowing you to auto-complete (or specify custom)
                  another user's preferred name to select them for rooming with.
              Anti-Roommate Requests:
                None or more input boxes allowing you to auto-complete (or specify custom)
                  another user's preferred name to select them for not rooming with.
              "Do you wish to only room with others in your department?"
                Yes/No Checkbox, where if yes, you must select your defatult department.
              Other Notes:
                Mutli-line textbox for other notes for admin review.
            -->
            <p>Please fill out our extended questionaire if you would like:</p>
            <!--
              "Do you prefer single gender housing?"
                Yes/No Checkbox, where if yes, you are displayed a textbox to specify your
                  self-identifying gender.
              "What is your preferred noise level?"
                Multiple-choice box, similar to how we ask for MAGStock
              "Do you smell of ash?"
                or... Do you care about be in a room with people who are smokers?
              "Do you have asthma?"
                similar to above question.
              "Are you a morning or evening person? Are you sleeping through the day or night?"
                Try to make sure people who sleep during the day together to reduce desturbances.
            -->
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
        checked: true,
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
            self.$store.commit('open_snackbar', 'It worked!');
          });
        } else {
          // TODO: Push the user back to Uber?
          // self.$store.commit('open_snackbar', 'Failed to log in. Are your credentials correct?');
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
