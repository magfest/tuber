<template>
  <div class="card">
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <div class="flex justify-content-between align-items-center flex-wrap gap-2">
      <h3 class="mt-0 mb-0">Room Assignments</h3>
      <div class="flex gap-2 align-items-center flex-wrap">
        <Dropdown v-model="block" :options="blocks" optionLabel="name" optionValue="id"
                  placeholder="Select a block" />
        <Dropdown v-model="matchNights" :options="matchNightsOptions" optionLabel="label" optionValue="value"
                  aria-label="Nights to match on"
                  title="Approved: only nights each person is approved for. Requested: every night they asked for, even with a missing shift." />
        <Button label="Suggest Rooms" icon="pi pi-star" @click="suggestRooms"
                :loading="suggesting" :disabled="!block" />
        <Button label="Rematch All" icon="pi pi-refresh" class="p-button-outlined"
                @click="rematchAll($event)" :disabled="!block" />
        <Button label="Clear Suggestions" icon="pi pi-trash" class="p-button-outlined p-button-danger"
                @click="clearSuggestions($event)" :disabled="!block" />
        <Button :label="selection.length ? 'New Room with ' + selection.length + ' selected' : 'New Room'"
                icon="pi pi-plus" class="p-button-outlined" @click="createRoom" :disabled="!block" />
      </div>
    </div>

    <div class="grid mt-2">
      <!-- Unassigned request pool. Keyed on the block so switching blocks mounts
           a fresh table (first page, empty selection) instead of mutating the
           old one while its last request may still be in flight. -->
      <div class="col-12 lg:col-5 request-pool">
        <div class="flex justify-content-between align-items-center">
          <h4>Unassigned Requests</h4>
          <span class="p-input-icon-left">
            <i class="pi pi-search" />
            <InputText v-model="poolSearch" placeholder="Search requests" @change="reloadPool" />
          </span>
        </div>
        <div class="filter-bar">
          <Dropdown v-model="poolNight" :options="nightOptions" optionLabel="label" optionValue="value"
                    placeholder="Any night" :showClear="poolNight !== null" title="Only people who requested this night" />
          <Dropdown v-model="poolApproval" :options="approvalOptions" optionLabel="label" optionValue="value"
                    title="Filter by night approval coverage" />
          <Dropdown v-model="poolSort" :options="poolSortOptions" optionLabel="label" optionValue="value"
                    title="Sort requests" />
          <div class="field-checkbox mb-0">
            <Checkbox inputId="poolroommates" v-model="poolRoommates" :binary="true" />
            <label for="poolroommates" title="Only people who requested specific roommates">Has roommates</label>
          </div>
        </div>
        <tuber-table v-if="block" :key="block" ref="pool" :url="poolUrl" tableTitle="" formTitle="Request"
                     :envelope="true" :parameters="poolParameters" :showActions="false" :showAdd="false"
                     :rows="10" :onSelect="setSelection">
          <template #controls><span></span></template>
          <template #columns>
            <Column selectionMode="multiple" headerStyle="width: 3em"></Column>
            <Column field="public_name" header="Name">
              <template #body="slotProps">
                <attendee-name :badge-id="slotProps.data.badge" :name="slotProps.data.public_name" />
              </template>
            </Column>
            <Column header="Nights">
              <template #body="slotProps">
                <div class="night-tags">
                  <Tag v-for="night in nightTags(slotProps.data)" :key="night.id" :severity="night.severity"
                       :value="night.short" :title="night.title" class="night-tag"
                       :class="{ 'night-tag-unrequested': !night.requested }" />
                </div>
              </template>
            </Column>
            <Column field="notes" header="Notes"></Column>
            <Column header="Admin Notes">
              <template #body="slotProps">
                <inline-note compact :modelValue="slotProps.data.admin_notes || ''"
                             @update:modelValue="slotProps.data.admin_notes = $event"
                             :save="(text) => saveRequestNote(slotProps.data.id, text)" />
              </template>
            </Column>
          </template>
        </tuber-table>
        <p v-else>Select a hotel block to see requests.</p>
      </div>

      <!-- Rooms -->
      <div class="col-12 lg:col-7">
        <div class="flex justify-content-between align-items-center flex-wrap gap-2">
          <h4>Rooms</h4>
          <span class="p-input-icon-left">
            <i class="pi pi-search" />
            <InputText v-model="roomSearch" placeholder="Room or roommate name" />
          </span>
        </div>
        <div class="filter-bar">
          <Dropdown v-model="roomStatus" :options="statusOptions" optionLabel="label" optionValue="value"
                    title="Filter by room status" />
          <Dropdown v-if="locations.length" v-model="roomLocation" :options="locationOptions"
                    optionLabel="label" optionValue="value" placeholder="Any location"
                    :showClear="roomLocation !== null" title="Filter by hotel location" />
          <Dropdown v-model="roomSort" :options="roomSortOptions" optionLabel="label" optionValue="value"
                    title="Sort rooms" />
        </div>
        <div class="room-cards">
          <!-- Suggested rooms come first; completing or locking one keeps it. -->
          <div v-if="suggestedRooms.length" class="suggested-header">
            <strong>{{ suggestedRooms.length }} suggested, awaiting review</strong>
            <Button label="Complete All" icon="pi pi-check-circle" class="p-button-sm p-button-success"
                    @click="completeAll($event)" />
          </div>
          <div v-for="room in suggestedRooms.concat(rooms)" :key="room.id" class="room-card"
               :class="{ 'room-completed': room.completed, 'room-suggested': room.suggested }">
            <div class="room-header">
              <span class="room-title">
                <room-name :room-id="room.id" :name="room.name" />
                <span class="error-count ml-2" v-if="room.suggested && errorCount(room)">
                  <i class="pi pi-exclamation-triangle" /> {{ errorCount(room) }}
                </span>
              </span>
              <div class="night-tags">
                <Tag v-for="night in roomNightTags(room)" :key="night.id" :severity="night.severity"
                     :value="night.short" :title="night.title" class="night-tag"
                     :class="{ 'night-tag-unrequested': !night.booked }" />
              </div>
              <div class="flex gap-1 room-actions">
                <Button :icon="room.completed ? 'pi pi-check-circle' : 'pi pi-circle'"
                        :class="['p-button-rounded p-button-text', room.completed ? 'p-button-success' : 'p-button-warning']"
                        :title="room.completed ? 'Completed — click to reopen' : 'Click to mark completed'"
                        @click="toggleRoomFlag(room, 'completed')" />
                <Button :icon="room.locked ? 'pi pi-lock' : 'pi pi-lock-open'"
                        :class="['p-button-rounded p-button-text', room.locked ? 'p-button-info' : 'p-button-warning']"
                        :title="room.locked ? 'Locked' : 'Unlocked'"
                        @click="toggleRoomFlag(room, 'locked')" />
                <Button icon="pi pi-user-plus" class="p-button-rounded p-button-text"
                        title="Add selected requests to this room"
                        :disabled="!selection.length" @click="addSelected(room)" />
                <Button icon="pi pi-star" class="p-button-rounded p-button-text"
                        title="Suggest roommates" @click="openSuggestions(room)" />
                <Button icon="pi pi-trash" class="p-button-rounded p-button-text p-button-danger"
                        title="Delete room" @click="removeRoom($event, room)" />
              </div>
            </div>
            <div class="occupants">
              <div v-for="mate in roomRoommates(room)" :key="mate.id" class="occupant"
                   :class="groupTag(room, mate) && groupTag(room, mate).className"
                   :title="groupTag(room, mate) && groupTag(room, mate).title">
                <div class="occupant-main">
                  <Button icon="pi pi-times" class="p-button-rounded p-button-text p-button-danger remove-mate"
                          :title="'Remove ' + mate.name + ' from this room'" :aria-label="'Remove ' + mate.name"
                          @click="removeRoommate(room, mate)" />
                  <attendee-name :badge-id="mate.id" :name="mate.name" />
                  <Chip v-for="error in otherErrors(mate)" :key="error" :label="error" class="error-chip" />
                  <Chip v-if="extraNightsError(mate)" class="error-chip">
                    <span>{{ extraNightsError(mate) }}</span>
                    <Button v-if="(mate.extra_nights || []).length" icon="pi pi-minus" class="p-button-rounded chip-button"
                            :title="'Remove the extra night(s) from ' + mate.name"
                            :aria-label="'Remove extra nights from ' + mate.name"
                            @click="removeExtraNights(room, mate)" />
                  </Chip>
                  <Chip v-for="wanted in mate.requested_missing" :key="'wanted' + wanted.id" class="error-chip">
                    <span>Requested {{ wanted.name }}</span>
                    <Button v-if="wanted.addable" icon="pi pi-plus" class="p-button-rounded chip-button"
                            :title="'Add ' + wanted.name + ' to this room'" :aria-label="'Add ' + wanted.name"
                            @click="addRoommates(room, [wanted.id])" />
                  </Chip>
                  <div v-if="mate.notes" class="staffer-note" :title="'From ' + mate.name + '\'s request'">
                    <i class="pi pi-comment" /> {{ mate.notes }}
                  </div>
                </div>
                <div v-if="mate.admin_notes" class="occupant-admin-note" title="Admin note — edit it from the room">
                  <i class="pi pi-pencil" /> {{ mate.admin_notes }}
                </div>
              </div>
              <div v-if="!roomRoommates(room).length" class="empty">Empty room</div>
            </div>
            <div class="room-note">
              <inline-note compact :modelValue="room.admin_notes || ''" label="room admin note"
                           placeholder="Add room admin note"
                           @update:modelValue="room.admin_notes = $event"
                           :save="(text) => saveRoomNote(room, text)" />
            </div>
          </div>
        </div>
        <Paginator v-if="roomCount > 25" :rows="25" :totalRecords="roomCount"
                   @page="onRoomPage($event)" />
      </div>
    </div>

    <!-- Roommate suggestions -->
    <Dialog v-model:visible="showSuggestions" modal :style="{ width: '45rem', maxWidth: '95vw' }">
      <template #header>
        <h3 class="mt-0 mb-0" v-if="suggestionRoom">
          Suggested roommates for {{ suggestionRoom.name }}
        </h3>
      </template>
      <p v-if="suggestionsLoading">Scoring candidates...</p>
      <p v-else-if="!suggestions.length">
        No candidates found — everyone in this block is either housed in a completed room
        or has no matching request.
      </p>
      <DataTable v-else :value="suggestions" class="p-datatable-sm">
        <Column field="name" header="Name">
          <template #body="slotProps">
            <attendee-name :badge-id="slotProps.data.badge" :name="slotProps.data.name" />
          </template>
        </Column>
        <Column field="score" header="Score" :sortable="true"></Column>
        <Column header="Fit">
          <template #body="slotProps">
            <Tag v-if="!slotProps.data.missing_in_room.length" severity="success" value="Covers all nights" />
            <Tag v-else severity="warning" :value="'Misses ' + slotProps.data.missing_in_room.length + ' night(s)'" />
            <Tag v-if="slotProps.data.current_room" severity="info" value="Will move rooms" class="ml-1" />
          </template>
        </Column>
        <Column header="">
          <template #body="slotProps">
            <Button icon="pi pi-user-plus" class="p-button-sm"
                    @click="addSuggested(slotProps.data)" />
          </template>
        </Column>
      </DataTable>
    </Dialog>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
  margin: 0.4rem 0 0.6rem 0;
}
.filter-bar .p-dropdown {
  min-width: 9rem;
}
.suggested-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.room-cards {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  max-height: 65vh;
  overflow-y: auto;
}
.room-card {
  border: 1px solid var(--surface-border, #dee2e6);
  border-radius: 6px;
  padding: 0.6rem 0.9rem;
}
.room-completed {
  opacity: 0.75;
  border-left: 4px solid var(--green-500, #22c55e);
}
.room-suggested {
  border-left: 4px solid var(--orange-400, #fbbf24);
  background: rgba(245, 158, 11, 0.07);
}
.occupants {
  margin-top: 0.4rem;
}
.occupants .empty {
  color: var(--text-color-secondary, #6c757d);
  font-style: italic;
}
.occupant {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.2rem;
}
.occupant-main {
  min-width: 0;
}
.occupant-admin-note {
  flex: 0 1 40%;
  text-align: right;
  font-size: 0.85rem;
  color: var(--text-color-secondary, #6c757d);
  white-space: pre-wrap;
}
.staffer-note {
  font-size: 0.85rem;
  font-style: italic;
  color: var(--text-color-secondary, #6c757d);
  margin-left: 1.2rem;
  white-space: pre-wrap;
}
.room-note {
  margin-top: 0.5rem;
  padding-top: 0.4rem;
  border-top: 1px dashed var(--surface-border, #dee2e6);
}
.room-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.25rem 0.5rem;
}
.room-title {
  flex: 1 1 auto;
  min-width: 0;
}
.room-actions {
  flex: none;
}
/* Sized so 10 nights fit on one line in both the request table and room headers. */
.night-tags {
  display: flex;
  flex-wrap: nowrap;
  gap: 0.1rem;
}

.night-tag {
  width: 1.25rem;
  flex: none;
  padding: 0.1rem 0;
  font-size: 0.65rem;
}
/* Tighter cells so most names fit on one line beside the nights. */
.request-pool :deep(.p-datatable-sm .p-datatable-tbody > tr > td),
.request-pool :deep(.p-datatable-sm .p-datatable-thead > tr > th) {
  padding: 0.3rem 0.25rem;
}
.request-pool :deep(.inline-note) {
  min-width: 6rem;
}

.night-tag-unrequested {
  background: var(--surface-400, #adb5bd);
  opacity: 0.4;
}

.error-chip {
  background: rgba(239, 68, 68, 0.15);
  margin-left: 0.3rem;
  font-size: 0.75rem;
}
.error-chip .chip-button, .remove-mate {
  width: 1.4rem;
  height: 1.4rem;
  padding: 0;
}
.error-chip .chip-button {
  margin-left: 0.35rem;
}
.remove-mate {
  margin-right: 0.3rem;
  vertical-align: middle;
}
.error-count {
  color: var(--orange-500, #f59e0b);
}
</style>

<script>
import { mapGetters } from 'vuex'
import { get, post, patch, del } from '../../lib/rest'
import TuberTable from '../../components/TuberTable.vue'
import AttendeeName from '../../components/rooming/modals/AttendeeName.vue'
import RoomName from '../../components/rooming/modals/RoomName.vue'
import InlineNote from '../../components/rooming/InlineNote.vue'
import { requestGroupTags } from '../../lib/requestGroups'
import { saveRequestAdminNote, saveRoomAdminNote } from '../../lib/adminNotes'

export default {
  name: 'RoomAssignments',
  components: {
    TuberTable,
    AttendeeName,
    RoomName,
    InlineNote
  },
  data: () => ({
    block: null,
    blocks: [],
    nights: [],
    locations: [],
    rooms: [],
    roomCount: 0,
    roomLoadSequence: 0,
    roomOffset: 0,
    roomSearch: '',
    roomSearchTimer: null,
    roomStatus: 'incomplete',
    roomLocation: null,
    roomSort: 'modified_desc',
    suggestedRooms: [],
    roomDetails: {},
    selection: [],
    matchNights: 'approved',
    matchNightsOptions: [
      { label: 'Match approved nights', value: 'approved' },
      { label: 'Match requested nights', value: 'requested' }
    ],
    poolSearch: '',
    poolNight: null,
    poolApproval: '',
    poolRoommates: false,
    poolSort: 'name_asc',
    suggesting: false,
    showSuggestions: false,
    suggestionRoom: null,
    suggestions: [],
    suggestionsLoading: false,
    approvalOptions: [
      { label: 'Any approval', value: '' },
      { label: 'Fully approved', value: 'full' },
      { label: 'Needs approval', value: 'partial' }
    ],
    poolSortOptions: [
      { label: 'Name A→Z', value: 'name_asc' },
      { label: 'Name Z→A', value: 'name_desc' },
      { label: 'Most nights', value: 'nights_desc' },
      { label: 'Fewest nights', value: 'nights_asc' },
      { label: 'Notes', value: 'notes_asc' }
    ],
    statusOptions: [
      { label: 'All rooms', value: '' },
      { label: 'Incomplete', value: 'incomplete' },
      { label: 'Completed', value: 'completed' },
      { label: 'Locked', value: 'locked' },
      { label: 'Unlocked', value: 'unlocked' }
    ],
    roomSortOptions: [
      { label: 'Recently modified', value: 'modified_desc' },
      { label: 'Name A→Z', value: 'name_asc' },
      { label: 'Name Z→A', value: 'name_desc' },
      { label: 'Newest', value: 'created_desc' },
      { label: 'Oldest', value: 'created_asc' }
    ]
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    poolUrl () {
      return '/api/event/<event>/hotel/' + this.block + '/request_search'
    },
    poolParameters () {
      const [sort, order] = this.poolSort.split('_')
      const params = {
        search_term: this.poolSearch || '',
        nights: this.matchNights,
        sort,
        order
      }
      if (this.poolNight) {
        params.night = this.poolNight
      }
      if (this.poolApproval) {
        params.approval = this.poolApproval
      }
      if (this.poolRoommates) {
        params.has_roommates = true
      }
      return params
    },
    nightOptions () {
      return [{ label: 'Any night', value: null }].concat(
        this.nights.map((night) => ({ label: night.name, value: night.id })))
    },
    locationOptions () {
      return [{ label: 'Any location', value: null }].concat(
        this.locations.map((location) => ({ label: location.name, value: location.id })))
    }
  },
  mounted () {
    this.load()
    window.addEventListener('detailmodal-changed', this.refresh)
  },
  unmounted () {
    window.removeEventListener('detailmodal-changed', this.refresh)
    clearTimeout(this.roomSearchTimer)
  },
  methods: {
    async load () {
      if (!this.event) {
        return
      }
      this.nights = await get('/api/event/' + this.event.id + '/hotel_room_night', { sort: 'date' })
      this.blocks = await get('/api/event/' + this.event.id + '/hotel_room_block', { sort: 'name' })
      this.locations = await get('/api/event/' + this.event.id + '/hotel_location', { sort: 'name' })
      const fromQuery = parseInt(this.$route.query.block)
      if (fromQuery && this.blocks.some((x) => x.id === fromQuery)) {
        this.block = fromQuery
      } else if (this.blocks.length && !this.block) {
        this.block = this.blocks[0].id
      }
    },
    async refresh () {
      await this.loadRooms()
      this.reloadPool()
    },
    reloadPool () {
      if (this.$refs.pool) {
        this.$refs.pool.load()
      }
    },
    setSelection (selection) {
      this.selection = selection
    },
    saveRequestNote (requestId, text) {
      return saveRequestAdminNote(this.event.id, requestId, text)
    },
    saveRoomNote (room, text) {
      return saveRoomAdminNote(this.event.id, room.id, text)
    },
    async loadRooms () {
      if (!this.event) {
        return
      }
      if (!this.block) {
        return
      }
      // Same overlap problem as TuberTable.load: a block or filter change
      // while a request is in flight must not let the old response win.
      const sequence = ++this.roomLoadSequence
      const [sort, order] = this.roomSort.split('_')
      const params = {
        hotel_block: this.block,
        suggested: false,
        sort,
        order,
        limit: 25,
        offset: this.roomOffset
      }
      if (this.roomStatus) {
        params.status = this.roomStatus
      }
      if (this.roomLocation) {
        params.hotel_location = this.roomLocation
      }
      if (this.roomSearch) {
        params.search = this.roomSearch
      }
      const found = await get('/api/event/' + this.event.id + '/hotel/room_search', params)
      const suggested = await get('/api/event/' + this.event.id + '/hotel_room', {
        full: true,
        hotel_block: this.block,
        suggested: true,
        completed: false,
        sort: 'id',
        order: 'asc'
      })
      const details = await this.loadRoomDetails(
        (found.hotel_rooms || []).concat(suggested).map((x) => x.id))
      if (sequence !== this.roomLoadSequence) {
        return
      }
      this.rooms = found.hotel_rooms || []
      this.roomCount = found.count || 0
      this.suggestedRooms = suggested
      this.roomDetails = details
    },
    async loadRoomDetails (ids) {
      if (!ids.length) {
        return {}
      }
      return get('/api/event/' + this.event.id + '/hotel/room_details',
        { rooms: ids.join(',') })
    },
    roomRoommates (room) {
      const details = this.roomDetails[room.id]
      if (!details) {
        return []
      }
      return Object.values(details.roommates).sort((a, b) => {
        // Keep each request group together, ahead of people on their own.
        const [x, y] = [this.groupTag(room, a), this.groupTag(room, b)]
        return (x ? x.index : 99) - (y ? y.index : 99)
      })
    },
    errorCount (room) {
      return this.roomRoommates(room).reduce((n, mate) => n + mate.errors.length, 0)
    },
    nightTags (request) {
      // Every night gets a chip so they line up down the table.
      return this.nights.map((night) => {
        const requested = !!request.requested_nights[night.id]
        const approved = !!request.approved_nights[night.id]
        return {
          id: night.id,
          short: night.name.slice(0, 2),
          title: night.name + ': ' + (approved ? 'approved' : (requested ? 'requested, not approved' : 'not requested')),
          requested,
          severity: approved ? 'success' : (requested ? 'warning' : null)
        }
      })
    },
    roomNightTags (room) {
      // Which nights the room holds, and how many people each night.
      const details = this.roomDetails[room.id]
      const counts = {}
      if (details) {
        Object.values(details.roommates).forEach((mate) => {
          Object.keys(mate.room_night_assignments).forEach((night) => {
            counts[night] = (counts[night] || 0) + 1
          })
        })
      }
      return this.nights.map((night) => {
        const count = counts[night.id] || 0
        return {
          id: night.id,
          short: night.name.slice(0, 2),
          title: night.name + ': ' + (count ? count + ' assigned' : 'not booked'),
          booked: !!count,
          severity: count ? 'success' : null
        }
      })
    },
    async suggestRooms () {
      this.suggesting = true
      try {
        const res = await post('/api/event/' + this.event.id + '/hotel/' + this.block + '/suggest_rooms', { nights: this.matchNights })
        this.$toast.add({
          severity: 'info',
          summary: res.created.length
            ? 'Created ' + res.created.length + ' suggested room(s)'
            : 'Nobody left to match',
          life: 3000
        })
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Matching Failed', life: 3000 })
      }
      this.suggesting = false
      this.refresh()
    },
    rematchAll (event) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'Discard current suggestions and produce a fresh batch?',
        icon: 'pi pi-exclamation-triangle',
        accept: async () => {
          await post('/api/event/' + this.event.id + '/hotel/' + this.block + '/rematch_all', { nights: this.matchNights })
          this.refresh()
        }
      })
    },
    clearSuggestions (event) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'Delete all suggested rooms that are not completed or locked?',
        icon: 'pi pi-exclamation-triangle',
        accept: async () => {
          await post('/api/event/' + this.event.id + '/hotel/' + this.block + '/clear_matches', {})
          this.refresh()
        }
      })
    },
    completeAll (event) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'Mark all ' + this.suggestedRooms.length + ' suggested rooms completed?',
        icon: 'pi pi-question-circle',
        accept: async () => {
          for (const room of this.suggestedRooms) {
            await patch('/api/event/' + this.event.id + '/hotel_room/' + room.id,
              { id: room.id, completed: true, suggested: false })
          }
          this.refresh()
        }
      })
    },
    async createRoom () {
      const room = await post('/api/event/' + this.event.id + '/hotel_room',
        { event: this.event.id, hotel_block: this.block, name: 'New Room' })
      if (this.selection.length) {
        await this.addSelected(room)
      } else {
        this.refresh()
      }
    },
    groupTag (room, mate) {
      // room_details groups are objects keyed by badge id.
      const details = this.roomDetails[room.id]
      if (!details) {
        return null
      }
      const names = {}
      Object.values(details.roommates).forEach((x) => { names[x.id] = x.name })
      const groups = (details.groups || []).map((group) => Object.keys(group).map(Number))
      return requestGroupTags(groups, names)[mate.id] || null
    },
    otherErrors (mate) {
      // Missing roommate requests get their own chips, with an add button.
      return mate.errors.filter((error) => !error.startsWith('Requested ') && !error.startsWith('Extra Room Night'))
    },
    extraNightsError (mate) {
      // The room may run nights they aren't eligible for without them holding
      // those nights; the chip still shows, just without the remove button.
      return mate.errors.find((error) => error.startsWith('Extra Room Night')) || null
    },
    async removeExtraNights (room, mate) {
      await post('/api/event/' + this.event.id + '/hotel/' + this.block +
        '/room/' + room.id + '/remove_nights', { badge: mate.id, nights: mate.extra_nights })
      this.refresh()
    },
    async addRoommates (room, roommates) {
      const res = await post('/api/event/' + this.event.id + '/hotel/' + this.block +
        '/room/' + room.id + '/add_roommates', { roommates, nights: this.matchNights })
      if (res && res.skipped && res.skipped.length) {
        this.$toast.add({
          severity: 'warn',
          summary: res.skipped.length + ' not added: no approved nights',
          detail: 'Switch to Requested nights to place them anyway.',
          life: 5000
        })
      }
      this.refresh()
    },
    async removeRoommate (room, mate) {
      await post('/api/event/' + this.event.id + '/hotel/' + this.block +
        '/room/' + room.id + '/remove_roommates', { roommates: [mate.id] })
      this.refresh()
    },
    async toggleRoomFlag (room, flag) {
      const payload = { id: room.id }
      payload[flag] = !room[flag]
      // Completing or locking a suggested room keeps it as a regular room.
      const kept = room.suggested && payload[flag]
      if (kept) {
        payload.suggested = false
      }
      await patch('/api/event/' + this.event.id + '/hotel_room/' + room.id, payload)
      Object.assign(room, payload)
      if (kept) {
        this.refresh()
        return
      }
      // Refetch when the status filter keys off the flag that just changed,
      // so a room completed under "Incomplete" (or unlocked under "Locked")
      // drops out of the list instead of lingering until the next reload.
      const filteredBy = {
        completed: ['completed', 'incomplete'],
        locked: ['locked', 'unlocked']
      }
      if (filteredBy[flag].includes(this.roomStatus)) {
        this.loadRooms()
      }
    },
    removeRoom (event, room) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'Delete this room? Occupants return to the pool.',
        icon: 'pi pi-exclamation-triangle',
        accept: async () => {
          await del('/api/event/' + this.event.id + '/hotel_room/' + room.id)
          this.refresh()
        }
      })
    },
    async addSelected (room) {
      const roommates = this.selection.map((x) => x.badge)
      if (!roommates.length) {
        return
      }
      this.selection = []
      if (this.$refs.pool) {
        this.$refs.pool.clearSelection()
      }
      await this.addRoommates(room, roommates)
    },
    async openSuggestions (room) {
      this.suggestionRoom = room
      this.showSuggestions = true
      this.suggestionsLoading = true
      this.suggestions = []
      try {
        this.suggestions = await get('/api/event/' + this.event.id + '/hotel/room/' +
          room.id + '/suggest_roommates', { limit: 10, nights: this.matchNights })
      } finally {
        this.suggestionsLoading = false
      }
    },
    async addSuggested (candidate) {
      await post('/api/event/' + this.event.id + '/hotel/' + this.block +
        '/room/' + this.suggestionRoom.id + '/add_roommates', { roommates: [candidate.badge], nights: this.matchNights })
      this.suggestions = this.suggestions.filter((x) => x.badge !== candidate.badge)
      this.refresh()
    },
    onRoomPage (event) {
      this.roomOffset = event.first
      this.loadRooms()
    },
    onRoomFilter () {
      this.roomOffset = 0
      this.loadRooms()
    }
  },
  watch: {
    event () {
      this.load()
    },
    block (value) {
      const query = Object.assign({}, this.$route.query)
      if (value) {
        query.block = String(value)
      } else {
        delete query.block
      }
      if (JSON.stringify(query) !== JSON.stringify(this.$route.query)) {
        this.$router.replace({ query })
      }
      this.onRoomFilter()
    },
    roomSearch () {
      clearTimeout(this.roomSearchTimer)
      this.roomSearchTimer = setTimeout(this.onRoomFilter, 300)
    },
    roomStatus () {
      this.onRoomFilter()
    },
    roomLocation () {
      this.onRoomFilter()
    },
    roomSort () {
      this.onRoomFilter()
    }
  }
}
</script>
