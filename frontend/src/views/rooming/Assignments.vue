<template>
  <div class="card">
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <div class="flex justify-content-between align-items-center flex-wrap gap-2">
      <h3 class="mt-0 mb-0">Room Assignments</h3>
      <div class="flex gap-2 align-items-center flex-wrap">
        <Dropdown v-model="block" :options="blocks" optionLabel="name" optionValue="id"
                  placeholder="Select a block" />
        <Button label="Suggest Rooms" icon="pi pi-star" @click="suggestRooms"
                :loading="suggesting" :disabled="!block" />
        <Button label="Rematch All" icon="pi pi-refresh" class="p-button-outlined"
                @click="rematchAll($event)" :disabled="!block" />
        <Button label="Clear Suggestions" icon="pi pi-trash" class="p-button-outlined p-button-danger"
                @click="clearSuggestions($event)" :disabled="!block" />
        <Button label="New Room" icon="pi pi-plus" class="p-button-outlined" @click="createRoom"
                :disabled="!block" />
      </div>
    </div>

    <!-- Suggested rooms awaiting review -->
    <div v-if="suggestedRooms.length" class="suggested-strip">
      <div class="flex justify-content-between align-items-center">
        <h4>Suggested Rooms — {{ suggestedRooms.length }} awaiting review</h4>
        <div class="flex gap-2">
          <Button label="Accept All" icon="pi pi-check" class="p-button-sm p-button-success"
                  @click="acceptAll($event)" />
          <Button label="Reject All" icon="pi pi-times" class="p-button-sm p-button-danger p-button-outlined"
                  @click="clearSuggestions($event)" />
        </div>
      </div>
      <div class="suggested-cards">
        <div v-for="room in suggestedRooms" :key="room.id" class="suggested-card">
          <div class="flex justify-content-between align-items-center">
            <room-name :room-id="room.id" :name="room.name" />
            <span class="error-count" v-if="errorCount(room)">
              <i class="pi pi-exclamation-triangle" /> {{ errorCount(room) }}
            </span>
          </div>
          <div class="occupants">
            <div v-for="mate in roomRoommates(room)" :key="mate.id">
              <attendee-name :badge-id="mate.id" :name="mate.name" />
              <Chip v-for="error in mate.errors" :key="error" :label="error" class="error-chip" />
            </div>
          </div>
          <div class="flex gap-2 mt-2">
            <Button label="Accept" icon="pi pi-check" class="p-button-sm p-button-success"
                    @click="acceptRoom(room)" />
            <Button label="Reject" icon="pi pi-times" class="p-button-sm p-button-danger p-button-outlined"
                    @click="rejectRoom(room)" />
          </div>
        </div>
      </div>
    </div>

    <div class="grid mt-2">
      <!-- Unassigned request pool -->
      <div class="col-12 lg:col-5">
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
            <Checkbox id="poolroommates" v-model="poolRoommates" :binary="true" />
            <label for="poolroommates" title="Only people who requested specific roommates">Has roommates</label>
          </div>
        </div>
        <tuber-table v-if="block" ref="pool" :url="poolUrl" tableTitle="" formTitle="Request"
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
                <Tag v-for="night in nightTags(slotProps.data)" :key="night.id" :severity="night.severity"
                     :value="night.name" class="mr-1 mb-1" />
              </template>
            </Column>
            <Column field="notes" header="Notes"></Column>
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
            <InputText v-model="roomSearch" placeholder="Room or roommate name" @change="onRoomFilter" />
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
          <div v-for="room in rooms" :key="room.id" class="room-card"
               :class="{ 'room-completed': room.completed, 'room-suggested': room.suggested }">
            <div class="flex justify-content-between align-items-center">
              <room-name :room-id="room.id" :name="room.name" />
              <div class="flex gap-1">
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
              <div v-for="mate in roomRoommates(room)" :key="mate.id">
                <attendee-name :badge-id="mate.id" :name="mate.name" />
                <Chip v-for="error in mate.errors" :key="error" :label="error" class="error-chip" />
              </div>
              <div v-if="!roomRoommates(room).length" class="empty">Empty room</div>
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
.suggested-strip {
  border: 1px solid var(--orange-300, #fcd34d);
  background: rgba(245, 158, 11, 0.07);
  border-radius: 8px;
  padding: 0.5rem 1rem;
  margin-top: 0.75rem;
}
.suggested-cards {
  display: flex;
  gap: 0.75rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
}
.suggested-card {
  border: 1px solid var(--surface-border, #dee2e6);
  border-radius: 6px;
  padding: 0.6rem;
  min-width: 16rem;
  background: var(--surface-card, white);
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
}
.occupants {
  margin-top: 0.4rem;
}
.occupants .empty {
  color: var(--text-color-secondary, #6c757d);
  font-style: italic;
}
.error-chip {
  background: rgba(239, 68, 68, 0.15);
  margin-left: 0.3rem;
  font-size: 0.75rem;
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

export default {
  name: 'RoomAssignments',
  components: {
    TuberTable,
    AttendeeName,
    RoomName
  },
  data: () => ({
    block: null,
    blocks: [],
    nights: [],
    locations: [],
    rooms: [],
    roomCount: 0,
    roomOffset: 0,
    roomSearch: '',
    roomStatus: 'incomplete',
    roomLocation: null,
    roomSort: 'modified_desc',
    suggestedRooms: [],
    roomDetails: {},
    selection: [],
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
    async loadRooms () {
      if (!this.event) {
        return
      }
      if (!this.block) {
        return
      }
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
      this.rooms = found.hotel_rooms || []
      this.roomCount = found.count || 0
      this.suggestedRooms = await get('/api/event/' + this.event.id + '/hotel_room', {
        full: true,
        hotel_block: this.block,
        suggested: true,
        completed: false,
        sort: 'id',
        order: 'asc'
      })
      await this.loadRoomDetails()
    },
    async loadRoomDetails () {
      const ids = this.rooms.map((x) => x.id).concat(this.suggestedRooms.map((x) => x.id))
      if (!ids.length) {
        this.roomDetails = {}
        return
      }
      this.roomDetails = await get('/api/event/' + this.event.id + '/hotel/room_details',
        { rooms: ids.join(',') })
    },
    roomRoommates (room) {
      const details = this.roomDetails[room.id]
      if (!details) {
        return []
      }
      return Object.values(details.roommates)
    },
    errorCount (room) {
      return this.roomRoommates(room).reduce((n, mate) => n + mate.errors.length, 0)
    },
    nightTags (request) {
      return this.nights.filter((night) => request.requested_nights[night.id]).map((night) => ({
        id: night.id,
        name: night.name,
        severity: request.approved_nights[night.id] ? 'success' : 'warning'
      }))
    },
    async suggestRooms () {
      this.suggesting = true
      try {
        const res = await post('/api/event/' + this.event.id + '/hotel/' + this.block + '/suggest_rooms', {})
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
          await post('/api/event/' + this.event.id + '/hotel/' + this.block + '/rematch_all', {})
          this.refresh()
        }
      })
    },
    clearSuggestions (event) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'Delete all unaccepted suggested rooms?',
        icon: 'pi pi-exclamation-triangle',
        accept: async () => {
          await post('/api/event/' + this.event.id + '/hotel/' + this.block + '/clear_matches', {})
          this.refresh()
        }
      })
    },
    async acceptRoom (room) {
      await patch('/api/event/' + this.event.id + '/hotel_room/' + room.id,
        { id: room.id, completed: true, suggested: false })
      this.refresh()
    },
    async rejectRoom (room) {
      await del('/api/event/' + this.event.id + '/hotel_room/' + room.id)
      this.refresh()
    },
    acceptAll (event) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'Accept all ' + this.suggestedRooms.length + ' suggested rooms?',
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
      await post('/api/event/' + this.event.id + '/hotel_room',
        { event: this.event.id, hotel_block: this.block, name: 'New Room' })
      this.refresh()
    },
    async toggleRoomFlag (room, flag) {
      const payload = { id: room.id }
      payload[flag] = !room[flag]
      if (flag === 'completed' && payload.completed && room.suggested) {
        payload.suggested = false
      }
      await patch('/api/event/' + this.event.id + '/hotel_room/' + room.id, payload)
      Object.assign(room, payload)
      if (flag === 'completed' && this.hideCompleted) {
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
      await post('/api/event/' + this.event.id + '/hotel/' + this.block +
        '/room/' + room.id + '/add_roommates', { roommates })
      this.selection = []
      this.refresh()
    },
    async openSuggestions (room) {
      this.suggestionRoom = room
      this.showSuggestions = true
      this.suggestionsLoading = true
      this.suggestions = []
      try {
        this.suggestions = await get('/api/event/' + this.event.id + '/hotel/room/' +
          room.id + '/suggest_roommates', { limit: 10 })
      } finally {
        this.suggestionsLoading = false
      }
    },
    async addSuggested (candidate) {
      await post('/api/event/' + this.event.id + '/hotel/' + this.block +
        '/room/' + this.suggestionRoom.id + '/add_roommates', { roommates: [candidate.badge] })
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
