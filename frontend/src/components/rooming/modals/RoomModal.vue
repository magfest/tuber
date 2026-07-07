<template>
  <Dialog :visible="visible" @update:visible="$emit('update:visible', $event)" modal
          :style="{ width: '65rem', maxWidth: '95vw' }" :dismissableMask="true">
    <template #header>
      <div v-if="room" class="flex align-items-center gap-2">
        <InputText v-model="room.name" @change="saveField('name')" class="room-name" />
        <Tag v-if="room.completed" severity="success" value="Completed" />
        <Tag v-else-if="room.suggested" severity="warning" value="Suggested" />
        <span v-if="room.hotel_block.name">{{ room.hotel_block.name }}</span>
        <span v-if="room.hotel_location.name">— {{ room.hotel_location.name }}</span>
      </div>
      <h3 v-else class="mt-0 mb-0">Loading...</h3>
    </template>

    <div v-if="room">
      <div class="flex gap-3 mb-3">
        <div class="field-checkbox mb-0">
          <Checkbox id="room-completed" v-model="room.completed" :binary="true"
                    @change="saveField('completed')" />
          <label for="room-completed">Completed</label>
        </div>
        <div class="field-checkbox mb-0">
          <Checkbox id="room-locked" v-model="room.locked" :binary="true"
                    @change="saveField('locked')" />
          <label for="room-locked">Locked</label>
        </div>
      </div>

      <p class="hint">Click a night cell to assign or unassign that night for that person.
         Green = assigned here, blue outline = requested and approved,
         orange outline = granted but not yet placed in a room, gray = not requested.</p>
      <table class="night-table">
        <thead>
          <tr>
            <th></th>
            <th v-for="night in room.nights" :key="night.id">
              {{ night.name }}<br><small>{{ night.date }}</small>
            </th>
            <th>Issues</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="occupant in room.occupants" :key="occupant.badge">
            <td class="occupant-name">
              <attendee-name :badge-id="occupant.badge" :name="occupant.name" />
            </td>
            <td v-for="night in room.nights" :key="night.id" class="night-cell"
                :class="cellClass(occupant, night)"
                :title="cellTitle(occupant, night)"
                @click="toggleNight(occupant, night)">
              <i v-if="occupant.nights[night.id].assigned" class="pi pi-check" />
              <i v-else-if="occupant.nights[night.id].assigned_room" class="pi pi-external-link" />
              <i v-else-if="occupant.nights[night.id].roomless" class="pi pi-home" />
            </td>
            <td>
              <Chip v-for="error in occupant.errors" :key="error" :label="error" class="error-chip" />
            </td>
            <td>
              <Button icon="pi pi-times" class="p-button-rounded p-button-danger p-button-text"
                      title="Remove from room" @click="removeOccupant(occupant)" />
            </td>
          </tr>
          <tr v-if="!room.occupants.length">
            <td :colspan="room.nights.length + 3">This room is empty.</td>
          </tr>
        </tbody>
      </table>

      <div class="grid mt-3">
        <div class="col-12 md:col-6">
          <h4>Messages (visible to occupants)</h4>
          <Textarea v-model="room.messages" rows="3" class="w-full" @change="saveField('messages')" />
        </div>
        <div class="col-12 md:col-6">
          <h4>Internal Notes</h4>
          <Textarea v-model="room.notes" rows="3" class="w-full" @change="saveField('notes')" />
        </div>
      </div>
    </div>
  </Dialog>
</template>

<style scoped>
.room-name {
  font-size: 1.2rem;
  font-weight: 600;
  width: 16rem;
}
.hint {
  color: var(--text-color-secondary, #6c757d);
  font-size: 0.9rem;
}
.night-table {
  border-collapse: collapse;
  width: 100%;
}
.night-table th, .night-table td {
  border: 1px solid var(--surface-border, #dee2e6);
  padding: 0.4rem 0.6rem;
  text-align: center;
}
.occupant-name {
  text-align: left;
  white-space: nowrap;
}
.night-cell {
  cursor: pointer;
  min-width: 3.5rem;
}
.night-cell.assigned {
  background: rgba(34, 197, 94, 0.25);
  color: var(--green-600, #16a34a);
}
.night-cell.wanted {
  box-shadow: inset 0 0 0 2px var(--blue-400, #60a5fa);
}
.night-cell.elsewhere {
  background: rgba(245, 158, 11, 0.2);
}
.night-cell.roomless {
  background: rgba(245, 158, 11, 0.12);
  box-shadow: inset 0 0 0 2px var(--orange-400, #fbbf24);
  color: var(--orange-500, #f59e0b);
}
.error-chip {
  background: rgba(239, 68, 68, 0.15);
  margin: 0.1rem;
  font-size: 0.8rem;
}
</style>

<script>
import { mapGetters } from 'vuex'
import { get, post, patch, del } from '../../../lib/rest'
import AttendeeName from './AttendeeName.vue'

export default {
  name: 'RoomModal',
  components: {
    AttendeeName
  },
  props: [
    'visible',
    'roomId'
  ],
  emits: [
    'update:visible',
    'changed'
  ],
  data: () => ({
    room: null,
    busy: false
  }),
  computed: {
    ...mapGetters([
      'event'
    ])
  },
  mounted () {
    this.load()
  },
  methods: {
    async load () {
      if (!this.roomId) {
        this.room = null
        return
      }
      this.room = null
      this.room = await get('/api/event/' + this.event.id + '/hotel/room/' + this.roomId + '/details')
    },
    cellClass (occupant, night) {
      const status = occupant.nights[night.id]
      if (status.assigned) {
        return 'assigned'
      }
      if (status.assigned_room) {
        return 'elsewhere'
      }
      if (status.roomless) {
        return 'roomless'
      }
      if (status.requested && status.approved) {
        return 'wanted'
      }
      return ''
    },
    cellTitle (occupant, night) {
      const status = occupant.nights[night.id]
      if (status.assigned) {
        return 'Assigned to this room — click to unassign'
      }
      if (status.assigned_room) {
        return 'Assigned to another room — click to move here'
      }
      if (status.roomless) {
        return 'Granted this night without a room — click to place here'
      }
      if (status.requested && status.approved) {
        return 'Requested and approved — click to assign'
      }
      if (status.requested) {
        return 'Requested but not approved — click to assign anyway'
      }
      return 'Not requested — click to assign anyway'
    },
    async clearNightAssignments (occupant, night) {
      // A night can carry several assignment rows (a room-less grant from the
      // attendee view plus a room assignment), so always clear them all before
      // writing a new one — a leftover NULL row otherwise shadows the update.
      const assignments = await get('/api/event/' + this.event.id + '/room_night_assignment',
        { badge: occupant.badge, room_night: night.id })
      for (const assignment of assignments) {
        await del('/api/event/' + this.event.id + '/room_night_assignment/' + assignment.id)
      }
    },
    async toggleNight (occupant, night) {
      if (this.busy) {
        return
      }
      this.busy = true
      const status = occupant.nights[night.id]
      try {
        await this.clearNightAssignments(occupant, night)
        if (status.assigned) {
          status.assigned = false
          status.assigned_room = null
        } else {
          await post('/api/event/' + this.event.id + '/room_night_assignment',
            { event: this.event.id, badge: occupant.badge, room_night: night.id, hotel_room: this.room.id })
          status.assigned = true
          status.assigned_room = this.room.id
        }
        status.roomless = false
        this.$emit('changed')
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Update Failed', life: 3000 })
        await this.load()
      }
      this.busy = false
    },
    async removeOccupant (occupant) {
      if (this.busy) {
        return
      }
      this.busy = true
      try {
        await post('/api/event/' + this.event.id + '/hotel/' + this.room.hotel_block.id +
          '/room/' + this.room.id + '/remove_roommates', { roommates: [occupant.badge] })
        this.$emit('changed')
        await this.load()
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Update Failed', life: 3000 })
        this.busy = false
        return
      }
      this.busy = false
    },
    async saveField (field) {
      try {
        const payload = { id: this.room.id }
        payload[field] = this.room[field]
        await patch('/api/event/' + this.event.id + '/hotel_room/' + this.room.id, payload)
        if (field === 'completed' && this.room.completed && this.room.suggested) {
          // Accepting a suggestion promotes it to a real room.
          await patch('/api/event/' + this.event.id + '/hotel_room/' + this.room.id,
            { id: this.room.id, suggested: false })
          this.room.suggested = false
        }
        this.$emit('changed')
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Save Failed', life: 3000 })
      }
    }
  },
  watch: {
    roomId () {
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
