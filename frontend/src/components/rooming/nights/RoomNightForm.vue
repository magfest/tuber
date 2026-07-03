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

        <div class="field">
            <label for="restriction_mode">Restriction</label><br>
            <Dropdown id="restriction_mode" v-model="roomNight.restriction_mode" :options="restrictionModes"
                      optionLabel="label" optionValue="value" />
        </div><br>

        <div class="field" v-if="restricted">
            <label for="restriction_type">Restriction Label</label><br>
            <InputText id="restriction_type" v-model="roomNight.restriction_type" /><br>
        </div><br v-if="restricted">

        <div class="field-checkbox" v-if="restricted">
            <Checkbox id="hidden" v-model="roomNight.hidden" :binary="true" />
            <label for="hidden">Hidden</label>
        </div>

        <template v-if="roomNight.restriction_mode === 'shift_window'">
            <p>The shift start and end times define the time window over which an overlapping
               shift will approve this night. Times are entered in the event's time zone
               ({{ eventTimeZone }}).</p>
            <div class="field">
              <label for="shift_starttime">Shift Start Time ({{ eventTimeZone }})</label><br>
              <input type="datetime-local" id="shift_starttime" v-model="shiftStarttimeInput" />
            </div>

            <div class="field">
              <label for="shift_endtime">Shift End Time ({{ eventTimeZone }})</label><br>
              <input type="datetime-local" id="shift_endtime" v-model="shiftEndtimeInput" />
            </div>
        </template>

        <template v-if="roomNight.restriction_mode === 'shift_hours'">
            <p>People with at least this many total assigned shift hours are approved for this night.</p>
            <div class="field">
              <label for="shift_hours_required">Shift Hours Required</label><br>
              <InputNumber id="shift_hours_required" v-model="roomNight.shift_hours_required"
                           :min="0" showButtons />
            </div>
        </template>

        <p v-if="roomNight.restriction_mode === 'manual'">
            This night requires a manual approval from a department head (on the Approvals page)
            or a rooming admin.
        </p>
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
      restriction_mode: 'none',
      restriction_type: '',
      shift_hours_required: null,
      hidden: false
    },
    restrictionModes: [
      { label: 'None — available to everyone', value: 'none' },
      { label: 'Shift within a time window', value: 'shift_window' },
      { label: 'Total shift hours', value: 'shift_hours' },
      { label: 'Manual approval', value: 'manual' }
    ]
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
    restricted () {
      return this.roomNight.restriction_mode && this.roomNight.restriction_mode !== 'none'
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
          if (!roomNight.restriction_mode) {
            roomNight.restriction_mode = roomNight.restricted ? 'shift_window' : 'none'
          }
          this.roomNight = roomNight
        })
      }
    },
    save () {
      // The backend mirrors restricted from restriction_mode, but send both so
      // older API versions behave sensibly too.
      this.roomNight.restricted = this.restricted
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
