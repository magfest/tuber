<template>
    <form @submit.prevent class="wideform">
        <div class="field-checkbox">
            <Checkbox id="decline" v-model="data.declined" :binary="true" />
            <label for="decline">Declined Space</label>
        </div>
        <div class="formgroup-inline">
            <div class="field">
                <label for="firstname" class="sr-only">First Name</label>
                <InputText v-model="data.first_name" id="firstname" type="text" placeholder="Firstname" />
            </div>
            <div class="field">
                <label for="lastname" class="sr-only">Last Name</label>
                <InputText v-model="data.last_name" id="lastname" type="text" placeholder="Lastname" />
            </div>
        </div>
        <div v-for="night in data.room_nights" :key="night.name" class="field-checkbox">
            <Checkbox v-model="night.requested" :id="night.name" :disabled="data.declined" :binary="true" />
            <label :for="night.name">{{ night.name }}</label>
        </div>
        <div class="field">
            <label for="notes">Notes</label><br>
            <Textarea id="notes" :rows="8" :cols="50" v-model="data.notes" />
        </div>
        <div class="field">
            <label for="requested">Roommate Requests</label><br>
            <AutoComplete v-model="data.roommate_requests" field="public_name" forceSelection :multiple="true" :suggestions="suggestedNames" @complete="completeNames($event)" />
        </div>
        <div class="field">
            <label for="antirequested">Anti-Roommate Requests</label><br>
            <AutoComplete v-model="data.roommate_anti_requests" field="public_name" forceSelection :multiple="true" :suggestions="suggestedNames" @complete="completeNames($event)" />
        </div>
    </form>
</template>

<style scoped>

</style>

<script>
import { mapGetters } from 'vuex'
export default {
  name: 'RequestShortForm',
  components: {
  },
  props: [
    'modelValue'
  ],
  computed: {
    ...mapGetters([
      'badges'
    ])
  },
  data () {
    return {
      data: this.modelValue,
      suggestedNames: []
    }
  },
  methods: {
    completeNames (event) {
      this.suggestedNames = []
      this.badges.forEach((badge) => {
        if (badge.search_name) {
          if (badge.search_name.toLowerCase().includes(event.query.toLowerCase())) {
            this.suggestedNames.push(badge)
          }
        }
      })
    }
  }
}
</script>
