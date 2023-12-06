<template>
    <form @submit.prevent class="wideform">
        <div class="field-checkbox">
            <Checkbox id="decline" v-model="data.declined" :binary="true" />
            <label for="decline">Declined Space</label>
        </div>
        <div class="formgroup-inline">
            <div class="field">
                <label for="firstname">First Name</label><br>
                <InputText v-model="data.first_name" id="firstname" type="text" placeholder="Firstname" />
            </div>
            <div class="field">
                <label for="lastname">Last Name</label><br>
                <InputText v-model="data.last_name" id="lastname" type="text" placeholder="Lastname" />
            </div>
        </div>
        <div class="formgroup-inline">
          <div class="field">
            <div v-for="night in data.room_nights" :key="night.name" class="field-checkbox">
                <Checkbox v-model="night.requested" :id="night.name" :disabled="data.declined" :binary="true" />
                <label :for="night.name">{{ night.name }}</label>
            </div>
          </div>
          <div>
            <div class="field">
                <label for="notes">Notes</label><br>
                <Textarea id="notes" :rows="8" :cols="75" v-model="data.notes" />
            </div>
            <div class="field">
                <label for="requested">Roommate Requests</label><br>
                <roommate-field label="Requested Roommates" v-model="data.requested_roommates" :badges="badges" :disabled="data.declined"></roommate-field>
            </div>
            <div class="field">
                <label for="antirequested">Anti-Roommate Requests</label><br>
                <roommate-field label="Anti-Requested Roommates" v-model="data.antirequested_roommates" :badges="badges" :disabled="data.declined"></roommate-field>
            </div>
            <div class="formgroup-inline">
              <div class="field-checkbox">
                <Checkbox class="my-n5" :disabled="data.declined" v-model="data.prefer_single_gender" :binary="true"/>
                <label for="single_gender">Wants single-gender</label>
              </div>

              <div class="field">
                <label for="single_gender">Gender</label><br>
                <InputText id="single_gender" :disabled="data.declined" counter="64" maxlength="64" v-model="data.preferred_gender" /><br>
              </div>
            </div>
          </div>
        </div>
    </form>
</template>

<style scoped>

</style>

<script>
import { mapGetters } from 'vuex'
import { get } from '../../../lib/rest'
import RoommateField from './RoommateField.vue'

export default {
  name: 'RequestShortForm',
  components: {
    RoommateField
  },
  props: [
    'modelValue'
  ],
  computed: {
    ...mapGetters([
      'event'
    ])
  },
  data () {
    return {
      data: this.modelValue,
      badges: []
    }
  },
  mounted () {
    this.load()
  },
  methods: {
    async load () {
      this.badges = await get('/api/event/' + this.event.id + '/badge')
    },
  }
}
</script>
