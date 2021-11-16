<template>
    <form @submit.prevent>
        <div class="field">
            <label for="name">Name</label><br>
            <InputText id="name" v-model="hotelLocation.name" /><br>
          </div><br>

          <div class="field">
            <label for="address">Address</label><br>
            <InputText id="address" v-model="hotelLocation.address" /><br>
          </div><br>
    </form>
</template>

<script>
import { mapGetters } from 'vuex'
import { get, post, patch } from '@/lib/rest'

export default {
  name: 'LocationForm',
  props: [
    'id'
  ],
  components: {
  },
  data: () => ({
    hotelLocation: {
      name: '',
      address: ''
    }
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    url () {
      if (this.id) {
        return '/api/event/' + this.event.id + '/hotel_location/' + this.id
      }
      return '/api/event/' + this.event.id + '/hotel_location'
    }
  },
  mounted () {
    this.load()
  },
  methods: {
    load () {
      if (this.id) {
        get(this.url).then((hotelLocation) => {
          this.hotelLocation = hotelLocation
        })
      }
    },
    save () {
      if (this.id) {
        return patch(this.url, this.hotelLocation).then(() => {
          this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 300 })
        }).catch(() => {
          this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 300 })
        })
      } else {
        return post(this.url, this.hotelLocation).then(() => {
          this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 300 })
        }).catch(() => {
          this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 300 })
        })
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
