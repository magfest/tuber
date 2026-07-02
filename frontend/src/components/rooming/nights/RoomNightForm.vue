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
      const tz = this.event ? this.event.timezone : null
      if (tz) {
        try {
          Intl.DateTimeFormat('en-US', { timeZone: tz })
          return tz
        } catch (e) {
          // fall through to the browser's zone if the event's is unusable
        }
      }
      return Intl.DateTimeFormat().resolvedOptions().timeZone
    },
    shiftStarttimeInput: {
      get () { return this.utcToEventInput(this.roomNight.shift_starttime) },
      set (val) { this.roomNight.shift_starttime = this.eventInputToUtc(val) }
    },
    shiftEndtimeInput: {
      get () { return this.utcToEventInput(this.roomNight.shift_endtime) },
      set (val) { this.roomNight.shift_endtime = this.eventInputToUtc(val) }
    }
  },
  mounted () {
    this.load()
  },
  methods: {
    // Wall-clock reading of a UTC instant in a time zone, encoded as a fake-UTC
    // millisecond timestamp so the parts can be read back with the getUTC* APIs.
    wallTimeInZone (ts, timeZone) {
      const dtf = new Intl.DateTimeFormat('en-US', {
        timeZone,
        hourCycle: 'h23',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
      const p = {}
      for (const part of dtf.formatToParts(new Date(ts))) {
        p[part.type] = part.value
      }
      return Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second)
    },
    // Convert a UTC value from the backend into the "YYYY-MM-DDTHH:mm" string
    // expected by <input type="datetime-local">, rendered in the event's zone.
    utcToEventInput (value) {
      if (!value) {
        return ''
      }
      const d = new Date(value)
      if (isNaN(d.getTime())) {
        return ''
      }
      const wall = new Date(this.wallTimeInZone(d.getTime(), this.eventTimeZone))
      const pad = (n) => String(n).padStart(2, '0')
      return `${wall.getUTCFullYear()}-${pad(wall.getUTCMonth() + 1)}-${pad(wall.getUTCDate())}T${pad(wall.getUTCHours())}:${pad(wall.getUTCMinutes())}`
    },
    // Convert a "YYYY-MM-DDTHH:mm" picker value (event-zone wall time) into a
    // UTC ISO string for the backend (which expects a trailing "Z").
    eventInputToUtc (value) {
      if (!value) {
        return null
      }
      const m = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/)
      if (!m) {
        return null
      }
      const wallAsUtc = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5])
      const tz = this.eventTimeZone
      // The zone offset depends on the instant (DST), which is what we are
      // solving for — iterate once to converge across DST boundaries.
      let ts = wallAsUtc - (this.wallTimeInZone(wallAsUtc, tz) - wallAsUtc)
      ts = wallAsUtc - (this.wallTimeInZone(ts, tz) - ts)
      return new Date(ts).toISOString()
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
