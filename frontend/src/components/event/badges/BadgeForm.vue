<template>
    <form @submit.prevent>
        <div class="field">
            <label for="printed_number">Printed Number</label><br>
            <InputText id="printed_number" v-model="badge.printed_number" /><br>
        </div><br>

        <div class="field">
            <label for="printed_name">Printed Name</label><br>
            <InputText id="printed_name" v-model="badge.printed_name" /><br>
            <small>This is the text printed on the physical badge.</small>
        </div><br>

        <div class="field">
            <label for="public_name">Public Name</label><br>
            <InputText id="public_name" v-model="badge.public_name" /><br>
            <small>This is used anywhere Tuber shows a name for a badge.</small>
        </div><br>

        <div class="field">
            <label for="legal_name">Legal Name</label><br>
            <InputText id="legal_name" v-model="badge.legal_name" /><br>
            <small>This is used by registration to verify photo id.</small>
        </div><br>

        <div class="field">
            <label for="phone">Phone</label><br>
            <InputText id="phone" v-model="badge.phone" /><br>
        </div><br>

        <div class="field">
            <label for="email">Email</label><br>
            <InputText id="email" v-model="badge.email" /><br>
        </div><br>

        <div class="field">
            <label for="emergency_contact_name">Emergency Contact</label><br>
            <InputText id="emergency_contact_name" v-model="badge.emergency_contact_name" /><br>
        </div><br>

        <div class="field">
            <label for="emergency_contact_phone">Emergency Contact Phone</label><br>
            <InputText id="emergency_contact_phone" v-model="badge.emergency_contact_phone" /><br>
        </div><br>
    </form>
</template>

<script>
import { mapGetters } from 'vuex'
import { get, patch } from '@/lib/rest'

export default {
  name: 'BadgeForm',
  props: [
    'id'
  ],
  components: {
  },
  data: () => ({
    badge: {
      printed_number: '',
      printed_name: '',
      public_name: '',
      legal_name: '',
      emergency_contact_name: '',
      emergency_contact_phone: '',
      phone: '',
      email: ''
    }
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    url () {
      if (this.id) {
        return '/api/event/' + this.event.id + '/badge/' + this.id
      }
      return '/api/event/' + this.event.id + '/badge'
    }
  },
  mounted () {
    this.load()
  },
  methods: {
    async load () {
      if (this.id) {
        this.badge = await get(this.url)
      }
    },
    async save () {
      try {
        await patch(this.url, this.badge)
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 300 })
      } catch (error) {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 300 })
      }
    }
  },
  watch: {
    event () {
      this.load()
    }
  }
}
</script>
