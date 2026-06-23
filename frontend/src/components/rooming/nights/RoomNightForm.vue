<template>
    <form @submit.prevent>
        <div class="field">
            <label for="name">Name</label><br>
            <InputText id="name" v-model="roomNight.name" /><br>
        </div><br>

        <div class="field">
            <label for="date">Date</label><br>
            <input type="date" id="date" v-model="roomNight.date" />
        </div><br>

        <div class="field-checkbox">
            <Checkbox id="restricted" v-model="roomNight.restricted" :binary="true" />
            <label for="restricted">Restricted</label>
        </div>

        <div class="field">
            <label for="restriction_type">Restriction Type</label><br>
            <InputText id="restriction_type" v-model="roomNight.restriction_type" :disabled="!roomNight.restricted"/><br>
        </div><br>

        <div class="field-checkbox">
            <Checkbox id="hidden" v-model="roomNight.hidden" :binary="true" :disabled="!roomNight.restricted"/>
            <label for="hidden">Hidden</label>
        </div>

        <p>For restricted nights, the shift start and end times define the time window over which an overlapping shift will approve this night.</p>
        <div class="field">
          <label for="shift_starttime">Shift Start Time</label><br>
          <input type="datetime-local" id="shift_starttime" v-model="shiftStarttimeLocal" :disabled="!roomNight.restricted" />
        </div>

        <div class="field">
          <label for="shift_endtime">Shift End Time</label><br>
          <input type="datetime-local" id="shift_endtime" v-model="shiftEndtimeLocal" :disabled="!roomNight.restricted" />
        </div>
    </form>
</template>

<script>
import { mapGetters } from 'vuex'
import { get, post, patch } from '../../../lib/rest'

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
    },
    // The backend stores shift times in UTC. The native datetime-local picker
    // works in the browser's local time, so we convert on read/write.
    shiftStarttimeLocal: {
      get () { return this.utcToLocalInput(this.roomNight.shift_starttime) },
      set (val) { this.roomNight.shift_starttime = this.localInputToUtc(val) }
    },
    shiftEndtimeLocal: {
      get () { return this.utcToLocalInput(this.roomNight.shift_endtime) },
      set (val) { this.roomNight.shift_endtime = this.localInputToUtc(val) }
    }
  },
  mounted () {
    this.load()
  },
  methods: {
    // Convert a UTC value from the backend into the "YYYY-MM-DDTHH:mm" string
    // expected by <input type="datetime-local">, rendered in local time.
    utcToLocalInput (value) {
      if (!value) {
        return ''
      }
      const d = new Date(value)
      if (isNaN(d.getTime())) {
        return ''
      }
      const pad = (n) => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
    },
    // Convert a local "YYYY-MM-DDTHH:mm" picker value into a UTC ISO string for
    // the backend (which expects a trailing "Z").
    localInputToUtc (value) {
      if (!value) {
        return null
      }
      const d = new Date(value)
      if (isNaN(d.getTime())) {
        return null
      }
      return d.toISOString()
    },
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
