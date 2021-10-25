<template>
  <div class="card" style="width: 1000px">
    <h3>Staff Hotel Room Request Form</h3>
    <div v-if="!badge">
      You do not current have a badge to this event.
    </div>
    <div v-else>
      <p><b>You are filling out this form as {{ badge.printed_name }}.</b></p>
      <form @submit.prevent>
        <p>These questions will help us find the best roommates for you. If you already have a group you'd like to room with the best way to be grouped
          together is to each request each other as roommates, and request the same nights. If this is your first time in staff housing or you don't
          know who you would like to room with then this form will help us match you with compatible roommates.</p>

        <p>Rooms are best-effort; we take your request details into consideration but cannot guarantee assignments will perfectly match requests.</p><br>

        <h4>Let us know if you don't want to apply for a room:</h4>
        <div class="field-checkbox">
          <Checkbox id="decline" v-model="request.decline" :binary="true" />
          <label for="decline">I do NOT want a staff room.</label>
        </div><br>

        <h4>Which nights would you like a room?</h4>
        <p>Nights marked "Setup" or "Teardown" will require department head approval. Talk to your department head for details.</p>
        <div v-for="night in request.room_nights" :key="night.name" class="field-checkbox">
          <Checkbox v-model="night.checked" :id="night.name" :disabled="request.decline" :binary="true" />
          <label :for="night.name">{{ night.restricted ? night.name + ' (' + night.restriction_type + ')' : night.name }}</label>
        </div>

        <p v-if="justification_required">Please provide justification for requesting restricted nights:</p>
        <Textarea v-model="request.justification" @input="blah" v-if="justification_required" :disabled="request.decline" :autoResize="true" rows="5" cols="50" placeholder="I'm helping with setup in <department>."></Textarea>
        <br><br>

        <h4>Who would you like to room with?</h4>
        <roommate-field label="Requested Roommates" v-model="request.requested_roommates" :disabled="request.decline"></roommate-field>
        <br>

        <h4>Who would you <b>not</b> like to room with?</h4>
        <roommate-field label="Anti-requested Roommates" v-model="request.antirequested_roommates" :disabled="request.decline"></roommate-field><br>

        <h4>Is there anything else we should know?</h4>
        <Textarea v-model="request.notes" rows="5" cols="50" :autoResize="true" :disabled="request.decline" outlined placeholder="I'm allergic to down pillows/I need to be able to take the stairs to my room/I like the view from the 19th floor and I see elevators as a challenge"></TextArea>

        <br><br>
        <Divider />
        <br>
        <p>The following questions are optional, but will help us match you with roommates.
          Note that the above roommate requests and anti-requests will take precedence over the below preferences.</p><br>

        <h4>Would you prefer to room with other people in your department?</h4>
        <div class="field-checkbox">
          <Checkbox :disabled="request.decline" v-model="request.prefer_department" :binary="true" />
          <label for="prefer_department">Yes, I would prefer to room with my department.</label>
        </div>
        <p v-if="request.prefer_department && departments.length > 1">You are assigned to multiple departments. Select your preferred department to room with:</p>
        <Dropdown :disabled="request.decline" :options="departments" v-if="request.prefer_department && departments.length > 1" optionLabel="name" v-model="request.preferred_department"></Dropdown>
        <p v-if="request.prefer_department && departments.length == 1">We will try to put you with the {{ departments[0].name }} department.</p><br>

        <h4>Would you prefer single gender rooming?</h4>
        <div class="field-checkbox">
          <Checkbox class="my-n5" :disabled="request.decline" v-model="request.single_gender" :binary="true"/>
          <label for="single_gender">Yes, I would prefer a single-gender room.</label>
        </div>
        <div v-if="request.single_gender" class="field">
          <label for="single_gender">What gender would you like to room with?</label><br>
          <InputText id="single_gender" :disabled="request.decline" counter="64" v-if="request.single_gender" v-model="request.gender" /><br>
          <small>We will do our best to group entries logically. I.e., males will be grouped with guys.</small>
        </div><br>

        <h4>What is your preferred noise level?</h4>
        <Dropdown :disabled="request.decline" v-model="request.noise_level" :options="noise_levels"></Dropdown><br><br>

        <h4>Would you prefer non-smoking roommates?</h4>
        <div class="field-checkbox">
          <Checkbox :disabled="request.decline" v-model="request.smoke_sensitive" :binary="true"/><br>
          <label for="smoke_sensitive">Yes, I would prefer non-smoking roommates.</label>
        </div><br>

        <h4>When do you plan to go to sleep?</h4>
        <Dropdown :disabled="request.decline" v-model="request.sleep_time" :options="sleep_times"></Dropdown>

      </form>
    </div>
  </div>
</template>

<style>
</style>

<script>
import { post } from '@/lib/rest'
import { mapGetters } from 'vuex'
import RoommateField from './RoommateField.vue'
import { ModelActionTypes } from '@/store/modules/models/actions'

export default {
  name: 'RoomRequest',
  components: {
    RoommateField
  },
  data: () => ({
    loading: false,
    roommates: [1, 2],
    confirmation: false,
    request: {
      decline: false,
      justification: '',
      requested_roommates: [],
      antirequested_roommates: [],
      room_nights: [
        {
          checked: true,
          name: 'Monday',
          restricted: true,
          restriction_type: 'Setup'
        }
      ]
    },
    noise_levels: [
      'Quiet - I am quiet, and prefer quiet.',
      "Moderate - I don't make a lot of noise.",
      "Loud - I'm ok if someone snores or I snore."
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
      'I have no idea.'
    ],
    alldepartments: [
      { id: 2, name: 'TechOps' },
      { id: 3, name: 'Not TechOps' }
    ],
    badge: {
      printed_name: 'Mark Murnane',
      departments: [
        2
      ]
    }
  }),
  computed: {
    ...mapGetters([
      'loggedIn',
      'event',
      'user'
    ]),
    justification_required () {
      if (!this.request.room_nights) {
        return false
      }
      for (let i = 0; i < this.request.room_nights.length; i += 1) {
        if (this.request.room_nights[i].restricted && this.request.room_nights[i].checked) {
          return true
        }
      }
      return false
    },
    departments () {
      const res = []
      for (let i = 0; i < this.alldepartments.length; i += 1) {
        if (this.badge.departments.indexOf(this.alldepartments[i].id) >= 0) {
          res.push(this.alldepartments[i])
        }
      }
      return res
    }
  },
  mounted () {
    this.$store.dispatch(ModelActionTypes.LOAD_BADGES)
  },
  methods: {
    addBadges () {
      post('/api/event/1/badge', {
        badge_type: 1,
        printed_name: 'Greg Murnane',
        search_name: 'greg murnane',
        first_name: 'Greg',
        last_name: 'Murnane',
        legal_name: 'Greg Murnane',
        legal_name_matches: true,
        phone: '2405479517',
        email: 'greg@magfest.org'
      })
      post('/api/event/1/badge', {
        badge_type: 1,
        printed_name: 'Josiah Tillett',
        search_name: 'josiah tillett',
        first_name: 'Josiah',
        last_name: 'Tillett',
        legal_name: 'Josiah Tillett',
        legal_name_matches: true,
        phone: '2405479517',
        email: 'josiah@magfest.org'
      })
      post('/api/event/1/badge', {
        badge_type: 1,
        printed_name: 'Josh Boy',
        search_name: 'josh boy',
        first_name: 'Josh',
        last_name: 'Boy',
        legal_name: 'Josh Boy',
        legal_name_matches: true,
        phone: '2405479517',
        email: 'josh@magfest.org'
      })
    },
    blah () {
      const len = this.request.justification.length
      const max = 200
      if (len > max) {
        this.request.justification = this.request.justification.slice(0, max)
        this.request.justification += 'blah '.repeat(Math.floor((len - max) / 5))
        if (this.request.justification.length < len) {
          this.request.justification += 'blah '.slice(0, (len % 5))
        }
      }
    },
    submitRequest () {
      const self = this
      self.loading = true
      self.post('/api/hotels/request', {
        badge: self.badge.id,
        request: self.request
      }).then(() => {
        self.loading = false
        self.confirmation = true
      }).catch(() => {
        self.notify('Failed to submit hotel request.')
        self.loading = false
      })
    }
  },
  watch: {
    event () {
      this.$store.dispatch(ModelActionTypes.LOAD_BADGES)
    }
  }
}
</script>
