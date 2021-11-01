<template>
  <div class="card">
    <Toast />
    <h3>Staff Hotel Room Request Form</h3>
    <div v-if="!badge">
      You do not current have a badge to this event.
    </div>
    <div v-else>
      <p><b>You are filling out this form as {{ badge.public_name }}.</b></p>
      <form @submit.prevent>
        <p>These questions will help us find the best roommates for you. If you already have a group you'd like to room with the best way to be grouped
          together is to each request each other as roommates, and request the same nights. If this is your first time in staff housing or you don't
          know who you would like to room with then this form will help us match you with compatible roommates.</p>

        <p>Rooms are best-effort; we take your request details into consideration but cannot guarantee assignments will perfectly match requests.</p><br>

        <h4>Let us know if you don't want to apply for a room:</h4>
        <div class="field-checkbox">
          <Checkbox id="decline" v-model="request.declined" :binary="true" />
          <label for="decline">I do NOT want a staff room.</label>
        </div><br>

        <div v-if="!request.declined">
          <h4>What name is on your photo ID?</h4>
          <p>The software used by our host hotel requires a first and last name. The front desk will compare these against your photo ID at checkin time. This will be shared only with STOPS and the hotel.</p>
          <div class="formgrid grid">
              <div class="field col">
                <label for="first_name">First Name</label>
                <InputText id="first_name" class="inputfield w-full" type="text" :disabled="request.declined" counter="64" v-model="request.first_name" />
              </div>
              <div class="field col">
                <label for="last_name">Last Name</label>
                <InputText id="last_name" class="inputfield w-full" type="text" :disabled="request.declined" counter="64" v-model="request.last_name" /><br>
              </div>
          </div>

          <h4>Which nights would you like a room?</h4>
          <p>Nights marked "Setup" or "Teardown" will require department head approval. Talk to your department head for details.</p>
          <div v-for="night in request.room_nights" :key="night.name" class="field-checkbox">
            <Checkbox v-model="night.requested" :id="night.name" :disabled="request.declined" :binary="true" />
            <label :for="night.name">{{ night.restricted ? night.name + ' (' + night.restriction_type + ')' : night.name }}</label>
          </div>

          <p v-if="justification_required">Please provide justification for requesting restricted nights:</p>
          <Textarea v-model="request.room_night_justification" @input="blah" v-if="justification_required" :disabled="request.declined" :autoResize="true" rows="5" cols="50" placeholder="I'm helping with setup in <department>."></Textarea>
          <br><br>

          <h4>Who would you like to room with?</h4>
          <roommate-field label="Requested Roommates" v-model="request.requested_roommates" :disabled="request.declined"></roommate-field>
          <br>

          <h4>Who would you <b>not</b> like to room with?</h4>
          <roommate-field label="Anti-requested Roommates" v-model="request.antirequested_roommates" :disabled="request.declined"></roommate-field><br>

          <p v-if="invalidRoommates">You cannot both request and anti-request a single person, and you can't request or anti-request yourself.</p>

          <h4>Would you prefer single gender rooming?</h4>
          <div class="field-checkbox">
            <Checkbox class="my-n5" :disabled="request.declined" v-model="request.prefer_single_gender" :binary="true"/>
            <label for="single_gender">Yes, I would prefer a single-gender room.</label>
          </div>

          <div class="field">
            <label for="single_gender">What is your gender?</label><br>
            <InputText id="single_gender" :disabled="request.declined" counter="64" v-model="request.preferred_gender" /><br>
            <small>This will be used to help match single-gender rooms. We will do our best to group entries logically.</small>
          </div><br>

          <h4>Is there anything else we should know?</h4>
          <Textarea v-model="request.notes" rows="5" cols="50" :autoResize="true" :disabled="request.declined" outlined placeholder="I'm allergic to down pillows/I need to be able to take the stairs to my room/I like the view from the 19th floor and I see elevators as a challenge"></TextArea>

          <br><br>
          <Divider />
          <br>
          <p>The following questions are optional, but will help us match you with roommates.
            Note that the above roommate requests and anti-requests will take precedence over the below preferences.</p><br>

          <h4>Would you prefer to room with other people in your department?</h4>
          <div class="field-checkbox">
            <Checkbox :disabled="request.declined" v-model="request.prefer_department" :binary="true" />
            <label for="prefer_department">Yes, I would prefer to room with my department.</label>
          </div>
          <p v-if="request.prefer_department && badge.departments.length > 1">You are assigned to multiple departments. Select your preferred department to room with:</p>
          <Dropdown :disabled="request.declined" :options="badge_departments" v-if="request.prefer_department && badge.departments.length > 1" optionValue="id" optionLabel="name" v-model="request.preferred_department"></Dropdown>
          <p v-if="request.prefer_department && badge.departments.length == 1">We will try to put you with the {{ badge.departments[0].name }} department.</p><br>

          <h4>What is your preferred noise level?</h4>
          <Dropdown :disabled="request.declined" v-model="request.noise_level" :options="noise_levels"></Dropdown><br><br>

          <h4>Would you prefer non-smoking roommates?</h4>
          <div class="field-checkbox">
            <Checkbox :disabled="request.declined" v-model="request.smoke_sensitive" :binary="true"/><br>
            <label for="smoke_sensitive">Yes, I would prefer non-smoking roommates.</label>
          </div><br>

          <h4>When do you plan to go to sleep?</h4>
          <Dropdown :disabled="request.declined" v-model="request.sleep_time" :options="sleep_times"></Dropdown><br><br>
        </div>

        <Button type="submit" :disabled="invalidRoommates" @click="saveRequest">Save</Button>

      </form>
    </div>
  </div>
</template>

<style>
</style>

<script>
import { get, post, patch } from '@/lib/rest'
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
      declined: false,
      room_night_justification: '',
      first_name: '',
      last_name: '',
      requested_roommates: [],
      antirequested_roommates: [],
      prefer_single_gender: false,
      preferred_gender: '',
      room_nights: []
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
    ]
  }),
  computed: {
    ...mapGetters([
      'loggedIn',
      'event',
      'user',
      'badge',
      'departmentLookup'
    ]),
    justification_required () {
      if (!this.request.room_nights) {
        return false
      }
      for (let i = 0; i < this.request.room_nights.length; i += 1) {
        if (this.request.room_nights[i].restricted && this.request.room_nights[i].requested) {
          return true
        }
      }
      return false
    },
    badge_departments () {
      const res = []
      for (let i = 0; i < this.badge.departments.length; i += 1) {
        if (Object.prototype.hasOwnProperty.call(this.departmentLookup, this.badge.departments[i])) {
          res.push(this.departmentLookup[this.badge.departments[i]])
        }
      }
      return res
    },
    invalidRoommates () {
      if (!this.request) {
        return false
      }
      for (const roommate of this.request.requested_roommates) {
        if (this.request.antirequested_roommates.includes(roommate)) {
          return true
        }
      }
      if (this.request.antirequested_roommates.includes(this.badge.id)) {
        return true
      }
      if (this.request.requested_roommates.includes(this.badge.id)) {
        return true
      }
      return false
    }
  },
  mounted () {
    this.$store.dispatch(ModelActionTypes.LOAD_BADGES)
    this.$store.dispatch(ModelActionTypes.LOAD_DEPARTMENTS)
    this.loadRequest()
  },
  methods: {
    loadRequest () {
      if (!this.event) {
        return {}
      }
      get('/api/event/' + this.event.id + '/hotel/request').then((request) => {
        this.request = request
      })
    },
    saveRequest () {
      patch('/api/event/' + this.event.id + '/hotel/request', this.request).then((request) => {
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', detail: 'Your request has been saved. You may continue editing it until the deadline.' })
      }).catch(() => {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.' })
      })
    },
    blah () {
      const len = this.request.room_night_justification.length
      const max = 200
      if (len > max) {
        this.request.room_night_justification = this.request.room_night_justification.slice(0, max)
        this.request.room_night_justification += 'blah '.repeat(Math.floor((len - max) / 5))
        if (this.request.room_night_justification.length < len) {
          this.request.room_night_justification += 'blah '.slice(0, (len % 5))
        }
      }
    },
    submitRequest () {
      post('/api/hotels/request', {
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
      this.loadRequest()
    }
  }
}
</script>
