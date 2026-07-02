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
      <h4>Room Request</h4>
      <Tag v-if="details.room_request && details.room_request.declined" severity="danger"
           value="Declined hotel space" class="mb-2" />
      <blockquote v-if="details.room_request && details.room_request.justification" class="justification">
        {{ details.room_request.justification }}
      </blockquote>
      <p v-else-if="details.room_request">No justification given for restricted nights.</p>
      <p v-else>This person has not started a room request.</p>

      <div class="night-grid">
        <div v-for="night in details.nights" :key="night.id"
             :class="['night-card', { 'night-missing': isMissing(night) }]">
          <div class="night-title">
            {{ night.name }}<br>
            <small>{{ night.date }}</small>
          </div>
          <div class="night-flags">
            <i class="pi" :class="night.requested ? 'pi-check-circle flag-on' : 'pi-minus-circle flag-off'"
               :title="night.requested ? 'Requested' : 'Not requested'" />
            <i v-if="night.restricted" class="pi pi-briefcase"
               :class="night.has_shift ? 'flag-on' : 'flag-bad'"
               :title="night.has_shift ? 'Has an overlapping shift' : 'No overlapping shift'" />
            <i class="pi pi-thumbs-up" :class="night.approved ? 'flag-on' : 'flag-off'"
               :title="night.approved ? 'Manually approved' : 'Not manually approved'" />
            <i class="pi pi-home" :class="night.assigned ? 'flag-on' : 'flag-off'"
               :title="night.assigned ? 'Assigned to the night' : 'Not assigned'" />
          </div>
          <small v-if="night.restricted" class="night-type">{{ night.restriction_type }}</small>
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
            <div v-for="(seg, i) in day.windows" :key="'w' + i" class="tl-window"
                 :style="segStyle(seg)" :title="seg.title"></div>
            <div v-for="(seg, i) in day.shifts" :key="'s' + i"
                 :class="['tl-shift', seg.overlaps ? 'tl-good' : 'tl-neutral']"
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
.night-missing {
  border-color: var(--red-500, #ef4444);
  background: var(--red-50, #fef2f2);
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
import { get } from '../../../lib/rest'
import { resolveTimeZone, wallTimeInZone, formatInZone } from '../../../lib/eventtime'

const DAY = 24 * 60 * 60 * 1000

export default {
  name: 'MissingShiftDetails',
  props: [
    'visible',
    'badgeId'
  ],
  emits: [
    'update:visible'
  ],
  data: () => ({
    details: null
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    timeZone () {
      return resolveTimeZone(this.event ? this.event.timezone : null)
    },
    // Restricted night windows and shifts as intervals in both real UTC ms
    // (for overlap math) and wall space (for layout).
    windows () {
      if (!this.details) {
        return []
      }
      return this.details.nights
        .filter((n) => n.restricted && n.shift_starttime && n.shift_endtime)
        .map((n) => {
          const start = new Date(n.shift_starttime).getTime()
          const end = new Date(n.shift_endtime).getTime()
          return {
            start,
            end,
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
        return {
          start,
          end,
          wallStart: wallTimeInZone(start, this.timeZone),
          wallEnd: wallTimeInZone(end, this.timeZone),
          overlaps: this.windows.some((w) => start < w.end && end > w.start),
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
      this.details = await get('/api/event/' + this.event.id + '/hotel/missing_shifts/' + this.badgeId)
    },
    isMissing (night) {
      return night.restricted && night.requested && !night.has_shift
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
