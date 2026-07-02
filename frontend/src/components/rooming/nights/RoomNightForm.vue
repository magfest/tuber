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

        <p>For restricted nights, the shift start and end times define the time window over which an overlapping shift will approve this night.
           Times are entered in the event's time zone ({{ eventTimeZone }}).</p>
        <div class="field">
          <label for="shift_starttime">Shift Start Time ({{ eventTimeZone }})</label><br>
          <input type="datetime-local" id="shift_starttime" v-model="shiftStarttimeInput" :disabled="!roomNight.restricted" />
        </div>

        <div class="field">
          <label for="shift_endtime">Shift End Time ({{ eventTimeZone }})</label><br>
          <input type="datetime-local" id="shift_endtime" v-model="shiftEndtimeInput" :disabled="!roomNight.restricted" />
        </div>
    </form>
</template>

<script>
import { mapGetters } from 'vuex'
import { get, post, patch } from '../../../lib/rest'
import { resolveTimeZone, utcToZoneInput, zoneInputToUtc } from '../../../lib/eventtime'

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
    // Shift windows are stored in UTC and compared against shift times, which
    // are also UTC. Staff may be anywhere, so the picker works in the event's
    // time zone rather than the browser's — everyone sees the same wall time.
    eventTimeZone () {
      return resolveTimeZone(this.event ? this.event.timezone : null)
    },
    shiftStarttimeInput: {
      get () { return utcToZoneInput(this.roomNight.shift_starttime, this.eventTimeZone) },
      set (val) { this.roomNight.shift_starttime = zoneInputToUtc(val, this.eventTimeZone) }
    },
    shiftEndtimeInput: {
      get () { return utcToZoneInput(this.roomNight.shift_endtime, this.eventTimeZone) },
      set (val) { this.roomNight.shift_endtime = zoneInputToUtc(val, this.eventTimeZone) }
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
          this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 3000 })
        }).catch(() => {
          this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 3000 })
        })
      } else {
        return post(this.url, this.roomNight).then(() => {
          this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 3000 })
        }).catch(() => {
          this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 3000 })
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
