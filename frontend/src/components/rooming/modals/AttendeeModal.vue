<template>
  <Dialog :visible="visible" @update:visible="$emit('update:visible', $event)" modal
          :style="{ width: '70rem', maxWidth: '95vw' }" :dismissableMask="true">
    <template #header>
      <div v-if="details">
        <h3 class="mb-1 mt-0">{{ details.name }}</h3>
        <div>
          <a :href="'mailto:' + details.email">{{ details.email }}</a>
          <span v-if="details.departments.length"> — {{ details.departments.join(', ') }}</span>
        </div>
      </div>
      <h3 v-else class="mt-0 mb-0">Loading...</h3>
    </template>

    <div v-if="details">
      <div class="grid">
        <div class="col-12 md:col-6">
          <h4>Room Request</h4>
          <Tag v-if="details.room_request && details.room_request.declined" severity="danger"
               value="Declined hotel space" class="mb-2" />
          <blockquote v-if="details.room_request && details.room_request.justification" class="justification">
            {{ details.room_request.justification }}
          </blockquote>
          <p v-else-if="details.room_request">No justification given for restricted nights.</p>
          <p v-else>This person has not started a room request.</p>
          <template v-if="details.room_request">
            <p v-if="details.room_request.notes"><b>Notes:</b> {{ details.room_request.notes }}</p>
            <p v-if="details.room_request.roommate_requests.length">
              <b>Requested roommates:</b>
              <span v-for="(mate, i) in details.room_request.roommate_requests" :key="mate.id">
                <attendee-name :badge-id="mate.id" :name="mate.name" /><span v-if="i < details.room_request.roommate_requests.length - 1">, </span>
              </span>
            </p>
            <p v-if="details.room_request.roommate_anti_requests.length">
              <b>Anti-requested:</b>
              <span v-for="(mate, i) in details.room_request.roommate_anti_requests" :key="mate.id">
                <attendee-name :badge-id="mate.id" :name="mate.name" /><span v-if="i < details.room_request.roommate_anti_requests.length - 1">, </span>
              </span>
            </p>
            <p class="preferences">
              <Tag v-if="details.room_request.prefer_single_gender" severity="info"
                   :value="'Single gender: ' + (details.room_request.preferred_gender || '?')" class="mr-1" />
              <Tag v-if="details.room_request.noise_level" severity="info"
                   :value="details.room_request.noise_level" class="mr-1" />
              <Tag v-if="details.room_request.sleep_time" severity="info"
                   :value="'Sleeps: ' + details.room_request.sleep_time" class="mr-1" />
              <Tag v-if="details.room_request.smoke_sensitive" severity="info"
                   value="Smoke sensitive" class="mr-1" />
            </p>
            <Button label="Edit Full Request" icon="pi pi-pencil" class="p-button-sm p-button-outlined"
                    @click="editingRequest = true" />
          </template>
        </div>
        <div class="col-12 md:col-6">
          <h4>Rooms</h4>
          <p v-if="!details.rooms.length">Not assigned to any room.</p>
          <div v-for="room in details.rooms" :key="room.id" class="room-summary">
            <room-name :room-id="room.id" :name="room.name" />
            <Tag v-if="room.completed" severity="success" value="Completed" class="ml-2" />
            <Tag v-else-if="room.suggested" severity="warning" value="Suggested" class="ml-2" />
            <Tag v-if="room.locked" severity="info" value="Locked" class="ml-2" />
            <span v-if="room.block_name" class="ml-2">({{ room.block_name }})</span>
            <div v-if="room.roommates.length" class="roommates">
              with
              <span v-for="(mate, i) in room.roommates" :key="mate.id">
                <attendee-name :badge-id="mate.id" :name="mate.name" /><span v-if="i < room.roommates.length - 1">, </span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <p class="hint">Click the icons to change whether a night is requested, approved, or assigned.
         Hover a night to highlight its shift window in the timeline below.</p>

      <div class="night-grid">
        <div v-for="night in details.nights" :key="night.id"
             :class="['night-card', { 'night-missing': isMissing(night), 'night-hover': hoverNight === night.id }]"
             @mouseenter="hoverNight = night.id" @mouseleave="hoverNight = null">
          <div class="night-title">
            {{ night.name }}<br>
            <small>{{ night.date }}</small>
          </div>
          <div class="night-flags">
            <i class="pi flag-btn" :class="night.requested ? 'pi-check-circle flag-on' : 'pi-minus-circle flag-off'"
               :title="(night.requested ? 'Requested' : 'Not requested') + ' — click to change'"
               role="button" @click="toggleRequested(night)" />
            <i v-if="night.restricted && night.mode !== 'manual'" class="pi pi-briefcase"
               :class="night.has_shift ? 'flag-on' : 'flag-bad'"
               :title="shiftTitle(night)" />
            <i class="pi pi-thumbs-up flag-btn" :class="night.approved ? 'flag-on' : 'flag-off'"
               :title="(night.approved ? 'Manually approved' : 'Not manually approved') + ' — click to change'"
               role="button" @click="toggleApproved(night)" />
            <i class="pi pi-home flag-btn" :class="night.assigned ? 'flag-on' : 'flag-off'"
               :title="(night.assigned ? 'Assigned to the night' : 'Not assigned') + ' — click to change'"
               role="button" @click="toggleAssigned(night)" />
          </div>
          <small v-if="night.restricted" class="night-type">{{ nightModeLabel(night) }}</small>
        </div>
      </div>

      <h4>Shift Schedule vs Shift Windows <small>({{ timeZone }})</small></h4>
      <p v-if="!details.shifts.length">No shifts are assigned to this person.</p>
      <div class="timeline" v-if="timelineDays.length">
        <div class="tl-row tl-header">
          <span class="tl-daylabel"></span>
          <div class="tl-track-header">
            <span v-for="h in [0, 6, 12, 18]" :key="h" class="tl-hour"
                  :style="{ left: (h / 24 * 100) + '%' }">{{ h }}:00</span>
          </div>
        </div>
        <div v-for="day in timelineDays" :key="day.key" class="tl-row">
          <span class="tl-daylabel">{{ day.label }}</span>
          <div class="tl-track">
            <div v-for="(seg, i) in day.windows" :key="'w' + i"
                 :class="['tl-window', segHighlight(seg.nightIds)]"
                 :style="segStyle(seg)" :title="seg.title"
                 @mouseenter="hoverNight = seg.nightIds[0]" @mouseleave="hoverNight = null"></div>
            <div v-for="(seg, i) in day.shifts" :key="'s' + i"
                 :class="['tl-shift', seg.overlaps ? 'tl-good' : 'tl-neutral', segHighlight(seg.nightIds)]"
                 :style="segStyle(seg)" :title="seg.title"></div>
          </div>
        </div>
        <div class="tl-legend">
          <span><span class="swatch tl-window"></span> Shift window (restricted night)</span>
          <span><span class="swatch tl-shift tl-good"></span> Shift covering a window</span>
          <span><span class="swatch tl-shift tl-neutral"></span> Other shift</span>
        </div>
      </div>

      <h4 v-if="details.shifts.length">Shifts</h4>
      <DataTable v-if="details.shifts.length" :value="details.shifts" class="p-datatable-sm">
        <Column field="job" header="Job"></Column>
        <Column field="department" header="Department"></Column>
        <Column header="Time">
          <template #body="slotProps">
            {{ shiftTimeLabel(slotProps.data) }}
          </template>
        </Column>
      </DataTable>

      <Dialog v-model:visible="editingRequest" modal :style="{ width: '60rem', maxWidth: '95vw' }">
        <template #header>
          <h3 class="mt-0 mb-0">Edit Request — {{ details.name }}</h3>
        </template>
        <request-form v-if="details.room_request" ref="requestForm" :id="details.room_request.id" />
        <template #footer>
          <Button label="Cancel" class="p-button-text" @click="editingRequest = false" />
          <Button label="Save" icon="pi pi-check" @click="saveRequest" />
        </template>
      </Dialog>
    </div>
  </Dialog>
</template>

<style scoped>
.justification {
  border-left: 4px solid var(--primary-color, #2196f3);
  margin: 0.5rem 0;
  padding: 0.25rem 0.75rem;
  font-style: italic;
}
.hint {
  color: var(--text-color-secondary, #6c757d);
  font-size: 0.9rem;
}
.room-summary {
  margin-bottom: 0.5rem;
}
.room-summary .roommates {
  font-size: 0.9rem;
  color: var(--text-color-secondary, #6c757d);
  margin-left: 1.25rem;
}
.night-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.75rem 0;
}
.night-card {
  border: 1px solid var(--surface-border, #dee2e6);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  min-width: 7.5rem;
  text-align: center;
}
/* Tint instead of a solid palette color so the theme's own text color
   stays legible in both light and dark modes. */
.night-missing {
  border-color: var(--red-500, #ef4444);
  background: rgba(239, 68, 68, 0.12);
}
.night-hover {
  outline: 2px solid var(--primary-color, #2196f3);
}
.night-title {
  font-weight: 600;
  margin-bottom: 0.25rem;
}
.night-flags {
  display: flex;
  justify-content: center;
  gap: 0.4rem;
  margin: 0.25rem 0;
}
.flag-btn { cursor: pointer; }
.flag-btn:hover { transform: scale(1.25); }
.flag-on { color: var(--green-600, #16a34a); }
.flag-off { color: var(--surface-400, #ced4da); }
.flag-bad { color: var(--red-500, #ef4444); }
.night-type { color: var(--text-color-secondary, #6c757d); }

.timeline { margin: 0.75rem 0; }
.tl-row {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}
.tl-daylabel {
  width: 7.5rem;
  flex: none;
  font-size: 0.85rem;
  text-align: right;
  padding-right: 0.75rem;
}
.tl-track-header {
  position: relative;
  flex: 1;
  height: 1.1rem;
  font-size: 0.7rem;
  color: var(--text-color-secondary, #6c757d);
}
.tl-hour { position: absolute; transform: translateX(-50%); }
.tl-track {
  position: relative;
  flex: 1;
  height: 2rem;
  background: var(--surface-100, #f8f9fa);
  background-image: repeating-linear-gradient(to right,
    var(--surface-300, #dee2e6) 0, var(--surface-300, #dee2e6) 1px,
    transparent 1px, transparent calc(100% / 24));
  border-radius: 4px;
  overflow: hidden;
}
.tl-window {
  position: absolute;
  top: 0;
  bottom: 0;
  background: var(--blue-200, #90caf9);
  opacity: 0.55;
}
.tl-shift {
  position: absolute;
  top: 20%;
  bottom: 20%;
  border-radius: 3px;
}
.tl-good { background: var(--green-500, #22c55e); }
.tl-neutral { background: var(--surface-500, #adb5bd); }
.tl-hilite {
  opacity: 1;
  outline: 2px solid var(--primary-color, #2196f3);
  z-index: 1;
}
.tl-dim { opacity: 0.15; }
.tl-legend {
  display: flex;
  gap: 1.25rem;
  font-size: 0.85rem;
  margin-top: 0.5rem;
}
.tl-legend .swatch {
  display: inline-block;
  width: 1rem;
  height: 0.7rem;
  position: static;
  margin-right: 0.3rem;
  vertical-align: baseline;
  opacity: 1;
}
</style>

<script>
import { mapGetters } from 'vuex'
import { get, post } from '../../../lib/rest'
import { resolveTimeZone, wallTimeInZone, formatInZone } from '../../../lib/eventtime'
import AttendeeName from './AttendeeName.vue'
import RoomName from './RoomName.vue'
import RequestForm from '../requests/RequestForm.vue'

const DAY = 24 * 60 * 60 * 1000

export default {
  name: 'AttendeeModal',
  components: {
    AttendeeName,
    RoomName,
    RequestForm
  },
  props: [
    'visible',
    'badgeId'
  ],
  emits: [
    'update:visible',
    'changed'
  ],
  data: () => ({
    details: null,
    hoverNight: null,
    busy: false,
    editingRequest: false
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    timeZone () {
      return resolveTimeZone(this.event ? this.event.timezone : null)
    },
    // Restricted night windows and shifts as intervals in both real UTC ms
    // (for overlap math) and wall space (for layout). nightIds ties each
    // segment back to the night cards for hover highlighting.
    windows () {
      if (!this.details) {
        return []
      }
      return this.details.nights
        .filter((n) => n.mode === 'shift_window' && n.shift_starttime && n.shift_endtime)
        .map((n) => {
          const start = new Date(n.shift_starttime).getTime()
          const end = new Date(n.shift_endtime).getTime()
          return {
            start,
            end,
            nightIds: [n.id],
            wallStart: wallTimeInZone(start, this.timeZone),
            wallEnd: wallTimeInZone(end, this.timeZone),
            title: n.name + ' window: ' + formatInZone(start, this.timeZone) +
              ' to ' + formatInZone(end, this.timeZone)
          }
        })
    },
    shiftBlocks () {
      if (!this.details) {
        return []
      }
      return this.details.shifts.map((s) => {
        const start = new Date(s.starttime).getTime()
        const end = start + (s.duration || 0) * 1000
        const covering = this.windows.filter((w) => start < w.end && end > w.start)
        return {
          start,
          end,
          nightIds: covering.map((w) => w.nightIds[0]),
          wallStart: wallTimeInZone(start, this.timeZone),
          wallEnd: wallTimeInZone(end, this.timeZone),
          overlaps: covering.length > 0,
          title: s.job + ': ' + formatInZone(start, this.timeZone) +
            ' to ' + formatInZone(end, this.timeZone)
        }
      })
    },
    timelineDays () {
      const intervals = this.windows.concat(this.shiftBlocks)
      const dayKeys = new Set()
      for (const item of intervals) {
        for (let key = Math.floor(item.wallStart / DAY); key * DAY < item.wallEnd; key++) {
          dayKeys.add(key)
        }
      }
      return [...dayKeys].sort((a, b) => a - b).map((key) => ({
        key,
        label: new Intl.DateTimeFormat('en-US', {
          timeZone: 'UTC', weekday: 'short', month: 'short', day: 'numeric'
        }).format(new Date(key * DAY)),
        windows: this.clipToDay(this.windows, key),
        shifts: this.clipToDay(this.shiftBlocks, key)
      }))
    }
  },
  mounted () {
    this.load()
  },
  methods: {
    async load () {
      if (!this.badgeId) {
        this.details = null
        return
      }
      this.details = null
      this.details = await get('/api/event/' + this.event.id + '/hotel/attendee/' + this.badgeId)
    },
    isMissing (night) {
      if (!night.restricted || !night.requested) {
        return false
      }
      if (night.mode === 'manual') {
        return !night.approved
      }
      return !night.has_shift
    },
    nightModeLabel (night) {
      if (night.mode === 'shift_hours') {
        return (night.restriction_type ? night.restriction_type + ' — ' : '') +
          'needs ' + night.hours_required + 'h, has ' + night.hours_assigned + 'h'
      }
      const labels = { shift_window: 'shift window', manual: 'manual approval' }
      return (night.restriction_type ? night.restriction_type + ' — ' : '') +
        (labels[night.mode] || night.mode)
    },
    shiftTitle (night) {
      if (night.mode === 'shift_hours') {
        return night.has_shift
          ? 'Has enough shift hours (' + night.hours_assigned + '/' + night.hours_required + 'h)'
          : 'Not enough shift hours (' + night.hours_assigned + '/' + night.hours_required + 'h)'
      }
      return night.has_shift ? 'Has an overlapping shift' : 'No overlapping shift'
    },
    segHighlight (nightIds) {
      if (this.hoverNight === null) {
        return ''
      }
      return nightIds.includes(this.hoverNight) ? 'tl-hilite' : 'tl-dim'
    },
    async toggle (night, url, field, value) {
      if (this.busy) {
        return
      }
      this.busy = true
      try {
        const payload = { badge: this.badgeId, room_night: night.id }
        payload[field] = value
        const res = await post('/api/event/' + this.event.id + url, payload)
        night[field] = res[field]
        this.$emit('changed')
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Update Failed', life: 3000 })
      }
      this.busy = false
    },
    toggleRequested (night) {
      this.toggle(night, '/hotel/attendee/request', 'requested', !night.requested)
    },
    toggleApproved (night) {
      this.toggle(night, '/hotel/attendee/approve', 'approved', !night.approved)
    },
    toggleAssigned (night) {
      this.toggle(night, '/hotel/attendee/assign', 'assigned', !night.assigned)
    },
    async saveRequest () {
      await this.$refs.requestForm.save()
      this.editingRequest = false
      this.$emit('changed')
      this.load()
    },
    clipToDay (intervals, dayKey) {
      const dayStart = dayKey * DAY
      const dayEnd = dayStart + DAY
      return intervals
        .filter((item) => item.wallStart < dayEnd && item.wallEnd > dayStart)
        .map((item) => Object.assign({}, item, {
          left: (Math.max(item.wallStart, dayStart) - dayStart) / DAY * 100,
          width: Math.max(0.5,
            (Math.min(item.wallEnd, dayEnd) - Math.max(item.wallStart, dayStart)) / DAY * 100)
        }))
    },
    segStyle (seg) {
      return { left: seg.left + '%', width: seg.width + '%' }
    },
    shiftTimeLabel (shift) {
      const start = new Date(shift.starttime).getTime()
      const end = start + (shift.duration || 0) * 1000
      return formatInZone(start, this.timeZone) + ' to ' +
        formatInZone(end, this.timeZone) + ' (' + this.timeZone + ')'
    }
  },
  watch: {
    badgeId () {
      this.load()
    },
    visible (val) {
      if (val) {
        this.load()
      }
    }
  }
}
</script>
