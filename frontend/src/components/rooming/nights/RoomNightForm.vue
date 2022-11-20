<template>
    <form @submit.prevent>
        <div class="field">
            <label for="name">Name</label><br>
            <InputText id="name" v-model="roomNight.name" /><br>
        </div><br>

        <div class="field">
            <label for="date">Date</label><br>
            <Calendar id="date" v-model="roomNight.date" dateFormat="yy-mm-dd" />
        </div><br>

        <div class="field-checkbox">
            <Checkbox id="restricted" v-model="roomNight.restricted" :binary="true" />
            <label for="restricted">Restricted</label>
        </div>

        <div class="field">
            <label for="restriction_type">Restriction Type</label><br>
            <InputText id="restriction_type" v-model="roomNight.restriction_type" /><br>
        </div><br>

        <div class="field-checkbox">
            <Checkbox id="hidden" v-model="roomNight.hidden" :binary="true" />
            <label for="hidden">Hidden</label>
        </div>
    </form>
</template>

<script>
import { mapGetters } from 'vuex'
import { get, post, patch } from '@/lib/rest'

export default {
  name: 'RoomNightForm',
  props: [
    'id'
  ],
  components: {
  },
  data: () => ({
    roomNight: {
      name: '',
      date: '',
      restricted: false,
      restriction_type: '',
      hidden: false
    }
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    url () {
      if (this.id) {
        return '/api/event/' + this.event.id + '/hotel_room_night/' + this.id
      }
      return '/api/event/' + this.event.id + '/hotel_room_night'
    }
  },
  mounted () {
    this.load()
  },
  methods: {
    load () {
      if (this.id) {
        get(this.url, { sort: 'date' }).then((roomNight) => {
          this.roomNight = roomNight
        })
      }
    },
    save () {
      if (this.id) {
        return patch(this.url, this.roomNight).then(() => {
          this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 300 })
        }).catch(() => {
          this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 300 })
        })
      } else {
        return post(this.url, this.roomNight).then(() => {
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
