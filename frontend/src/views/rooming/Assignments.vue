<template>
  <div class="card">
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <h3>Room Assignments</h3>
    <Toolbar class="mb-1">
      <template #start>
        <Button class="p-button-success mr-2" @click="createRoom" :disabled="block === null">Create Room</Button>
        <Button class="p-button-info mr-2" @click="rematchAll($event)" :disabled="block === null">Rematch All</Button>
        <Button class="p-button-info mr-2" @click="clearAutoMatches($event)" :disabled="block === null">Reset Auto
          Matches</Button>
      </template>

      <template #end>
        <label for="blockselect" class="mr-2">Room Block</label>
        <Dropdown id="blockselect" :options="blocks" showClear v-model="block" optionLabel="name" optionValue="id" />
      </template>
    </Toolbar>

    <Dialog v-model:visible="editingRequest" :breakpoints="{ '1500px': '50vw', '1000px': '75vw', '500px': '95vw' }"
      :style="{ width: '50vw' }">
      <template #header>
        <h3>Hotel Room Request</h3>
      </template>

      <request-short-form :modelValue="editedRequest" />

      <template #footer>
        <Button label="Cancel" @click="cancelRequest" icon="pi pi-times" class="p-button-text" />
        <Button label="Save" @click="saveRequest(editedRequest)" icon="pi pi-check" autofocus />
      </template>
    </Dialog>

    <div class="grid">
      <div class="col">
        <DataTable class="p-datatable-sm" ref="dt" :lazy="true" selectionMode="multiple" :value="filteredRequests"
          :paginator="true" :rows="25" dataKey="id" v-model:filters="requestFilters" filterDisplay="row"
          :globalFilterFields="['public_name']" v-model:selection="selectedRequests" :totalRecords="totalRequests"
          :loading="loading" @page="onPage($event)" @sort="onSort($event)" @filter="onFilter($event)"
          v-if="block != null">
          <Column>
            <template #body="slotProps">
              <Button @click="editRequest(slotProps.data)" icon="pi pi-cog" class="p-button-info minibutton"
                iconPos="right" />
            </template>
          </Column>
          <Column header="Name" field="first_name" filterField="first_name" :sortable="true">
            <template #body="slotProps">
              {{ badgeLookup[slotProps.data.badge] != undefined ? badgeLookup[slotProps.data.badge].public_name :
                "loading" }}
            </template>
            <template #filter="{ filterModel, filterCallback }">
              <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"
                :placeholder="`Search Requests`" v-tooltip.top.focus="'Hit enter key to filter'" />
            </template>
          </Column>
          <Column style="width: 25%">
            <template #body="slotProps">
              <Tag v-for="night in roomNights" :key="'rn' + night.id" :value="night.name.slice(0, 2)"
                :severity="slotProps.data.nights[night.id] ? 'primary' : (slotProps.data.nights_requested[night.id] ? 'warning' : 'danger')"
                class="mr-1" style="width: 18px" />
            </template>
          </Column>
          <Column header="Notes" field="notes" filterField="notes" :sortable="true"></Column>
        </DataTable>
        <h3 v-else>
          Select a room block to search for people
        </h3>
      </div>

      <div class="col">
        <div class="flex justify-content-between">
          <span class="field-checkbox pt-2">
            <Checkbox id="hidecomplete" v-model="hidecompleted" :binary="true" />
            <label for="hidecomplete">Hide Completed</label>
          </span>
          <span class="p-input-icon-left pt-1">
            <i class="pi pi-search" />
            <InputText type="text" v-model="roomSearchText" placeholder="Search Rooms" @change="roomSearch" />
          </span>
        </div>
        <Card v-for="room in filteredRooms" :key="'rm' + room.id" class="mb-2">
          <template #title>
            <div class="flex justify-content-between">
              <span>
                <Button class="p-button-success mr-2" icon="pi pi-plus" @click="addRoommates(room)" />
                <Button v-if="room.completed" class="p-button-success mr-2" icon="pi pi-check-square"
                  @click="completeRoom(room, false)" />
                <Button v-else class="p-button-warning mr-2" icon="pi pi-stop" @click="completeRoom(room, true)" />
                <Button v-if="room.locked" class="p-button-success mr-2" icon="pi pi-lock"
                  @click="lockRoom(room, false)" />
                <Button v-else class="p-button-warning mr-2" icon="pi pi-unlock" @click="lockRoom(room, true)" />
                <InputText v-if="room.edit" v-model="room.name" @blur="saveRoom(room)" />
                <span v-else @click="room.edit = true">
                  {{ room.name ? room.name : "Unnamed" }}
                </span>
              </span>
              <span>
                <span class="external-block mr-2">{{ room.hotel_block != block ? (blockLookup[room.hotel_block] !=
                  undefined ? "(" + blockLookup[room.hotel_block].name + ")" : "loading") : "" }}</span>
                <Button class="p-button-info mr-2" icon="pi pi-info-circle" @click="roomInfo(room)" />
                <Button class="p-button-danger" @click="removeRoom(room)">Remove</Button>
              </span>
            </div>
          </template>
          <template #content>
            <div class="grid">
              <div class="col">
                <div v-for="roommate in room.roommates" :key="room.id + '_' + roommate">
                  <Button class="p-button-danger minibutton" icon="pi pi-times" iconPos="right"
                    @click="removeRoommate(room, roommate)" />
                  <Button @click="editRequestByBadge(roommate)" icon="pi pi-cog" class="p-button-info minibutton"
                    iconPos="right" />
                  {{ badgeLookup[roommate] != undefined ? badgeLookup[roommate].public_name : "loading" }}
                </div>
              </div>
              <div class="col notebox">
                Messages
                <Textarea v-model="room.messages" rows="3" @change="saveRoom(room)" />
              </div>
              <div class="col notebox">
                Internal Notes
                <Textarea v-model="room.notes" rows="3" @change="saveRoom(room)" />
              </div>
            </div>
          </template>
        </Card>
        <Paginator :totalRecords="roomCount" :rows="10" :first="roomOffset" @page="roomPage($event)"></Paginator>
      </div>
    </div>

    <Dialog v-model:visible="showRoomInfo" :breakpoints="{ '1500px': '50vw', '1000px': '75vw', '500px': '95vw' }"
      :style="{ width: '50vw' }">
      <template #header>
        <h3>{{ currentRoom.name }}</h3>
      </template>

      <div>
        <div v-for="group in roomDetails[currentRoom.id].groups" :key="Object.keys(group)[0] + '_group'"
          class="roommate_group">
          <div v-for="roommate in group" :key="currentRoom.id + '_' + roommate.id">
            {{ roommate.name }}
            <Chip v-for="error in roommate.errors" :key="roommate.id + error" :label="error" />
          </div>
        </div>
      </div>

      <template #footer>
        <Button label="Close" @click="cancelInfo" icon="pi pi-times" class="p-button-text" />
      </template>
    </Dialog>
  </div>
</template>

<style>
.roommate_group {
  margin-bottom: 5px;
}

.roommate_group:nth-child(2) {
  background: darkblue;
}

.roommate_group:nth-child(3) {
  background: darkgreen;
}

.roommate_group:nth-child(4) {
  background: darkred;
}

.p-chip {
  height: 15px;
  font-size: x-small;
}

.notebox .p-inputtext {
  width: 100%
}

.p-card .p-card-content {
  padding-top: 0;
  padding-bottom: 0;
}

.p-button.p-button-icon-only.minibutton {
  padding-top: 0;
  padding-bottom: 0;
  width: 19px;
  margin-bottom: 2px;
  margin-right: 2px;
}
</style>

<script>
import { reactive } from 'vue'
import { mapGetters } from 'vuex'
import { get, post, patch, del } from '../../lib/rest'
import { FilterMatchMode } from 'primevue/api'
import { ModelActionTypes } from '../../store/modules/models/actions'
import RequestShortForm from '../../components/rooming/requests/RequestShortForm.vue'

export default {
  name: 'RoomAssignments',
  props: [
    ''
  ],
  components: {
    RequestShortForm
  },
  data: () => ({
    roomSearchText: '',
    badges: [],
    blocks: [],
    block: '',
    loading: false,
    hidecompleted: true,
    requests: [],
    rooms: [],
    requestFilters: {
      global: { value: null, matchMode: FilterMatchMode.CONTAINS },
      notes: { value: null, matchMode: FilterMatchMode.CONTAINS },
      first_name: { value: null, matchMode: FilterMatchMode.CONTAINS }
    },
    roomFilters: {
      global: { value: null, matchMode: FilterMatchMode.CONTAINS },
      name: { value: null, matchMode: FilterMatchMode.CONTAINS }
    },
    selectedRequests: [],
    selectedRooms: [],
    roomNights: [],
    assignedNights: {},
    lazyParams: {},
    totalRequests: 0,
    filteredRequests: [],
    roomCount: 0,
    roomOffset: 0,
    showRoomInfo: false,
    roomDetails: {},
    currentRoom: null,
    editingRequest: false,
    editedRequest: null,
    editedRequestID: null
  }),
  computed: {
    ...mapGetters([
      'event',
      'departments'
    ]),
    filteredRooms() {
      const filtered = []
      for (const room of this.rooms) {
        if (this.hidecompleted) {
          if (!room.completed) {
            filtered.push(room)
          }
        } else {
          filtered.push(room)
        }
      }
      return filtered.slice(0, 10)
    },
    roomNightLookup() {
      const lookup = {}
      for (const night of this.roomNights) {
        lookup[night.id] = night
      }
      return lookup
    },
    badgeLookup() {
      const lookup = {}
      this.badges.forEach((badge) => {
        lookup[badge.id] = badge
      })
      return lookup
    },
    blockLookup() {
      const lookup = {}
      this.blocks.forEach((block) => {
        lookup[block.id] = block
      })
      return lookup
    }
  },
  mounted() {
    this.lazyParams = {
      first: 0,
      rows: this.$refs.dt.rows,
      sortField: 'first_name',
      sortOrder: 1,
      filters: this.requestFilters
    }
    if (this.event) {
      get('/api/event/' + this.event.id + '/hotel_room_night', { sort: 'date' }).then((roomNights) => {
        this.roomNights = roomNights
        this.getblocks().then(() => {
          this.load()
        })
      })
    }
  },
  methods: {
    async getblocks() {
      this.blocks = await get('/api/event/' + this.event.id + '/hotel_room_block', { sort: 'name' })
      if (this.blocks) {
        this.block = this.blocks[0].id
      }
    },
    async load() {
      this.loading = true
      this.roomOffset = 0
      this.badges = await get('/api/event/' + this.event.id + '/badge')
      await this.fetchRooms()
      await this.$store.dispatch(ModelActionTypes.LOAD_DEPARTMENTS)
      this.loading = false
    },
    async fetchRooms() {
      this.loading = true
      try {
        if (this.roomSearchText) {
          const result = await get('/api/event/' + this.event.id + '/hotel/room_search', { search: this.roomSearchText, offset: this.roomOffset })
          this.roomCount = result.count
          this.rooms = result.hotel_rooms
        } else {
          let query = { full: true, limit: 25, offset: this.roomOffset, sort: 'modified', order: 'desc', count: true };
          if (this.block != null) {
            query.hotel_block = this.block;
          }
          if (this.hidecompleted) {
            query.completed = false;
          }
          this.roomCount = await get('/api/event/' + this.event.id + '/hotel_room', query);
          delete query.count;
          this.rooms = await get('/api/event/' + this.event.id + '/hotel_room', query);
        }
      } catch (error) {
        this.rooms = []
      }
      this.loading = false
    },
    async fetchRequests() {
      this.loading = true
      try {
        if (this.block === null) {
          this.filteredRequests = [];
          return
        }
        let requests = []
        const searchRes = await get('/api/event/' + this.event.id + '/hotel/' + this.block + '/request_search', {
          approved: true,
          assigned: false,
          search_term: this.lazyParams.filters.first_name.value != null ? this.lazyParams.filters.first_name.value : "",
          full: true,
          deep: true,
          offset: this.lazyParams.first,
          limit: this.lazyParams.rows,
          sort: this.lazyParams.sortField,
          order: this.lazyParams.sortOrder > 0 ? 'asc' : 'desc'
        })
        requests = searchRes.requests
        this.totalRequests = searchRes.count

        const filtered = []
        for (const req of requests) {
          req.room_nights = []
          req.nights = {}
          req.nights_requested = {}
          for (const rn of this.roomNights) {
            const night = {
              name: rn.name,
              id: rn.id,
            }
            let requested = false
            let approved = false
            for (const nightreq of req.room_night_requests) {
              if (nightreq.room_night === rn.id && nightreq.requested) {
                requested = true
                break
              }
            }
            if (rn.restricted && requested) {
              for (const nightapp of req.room_night_approvals) {
                if (nightapp.room_night === rn.id && nightapp.approved) {
                  approved = true
                  break
                }
              }
            } else {
              approved = requested
            }
            night.requested = requested;
            req.nights[rn.id] = approved
            req.nights_requested[rn.id] = requested
            req.room_nights.push(night)
          }
          filtered.push(req)
        }
        this.filteredRequests = reactive(filtered)
      } catch (error) {
        this.filteredRequests = []
        this.totalRequests = 0
      }
      this.loading = false
    },
    onPage(event) {
      this.lazyParams = event
      this.fetchRequests()
    },
    async roomPage(event) {
      this.roomOffset = event.first
      await this.fetchRooms()
    },
    onSort(event) {
      this.lazyParams = event
      this.fetchRequests()
    },
    onFilter() {
      this.lazyParams.first = 0
      this.lazyParams.filters = this.requestFilters
      this.fetchRequests()
    },
    async createRoom() {
      this.roomOffset = 0
      const room = await post('/api/event/' + this.event.id + '/hotel_room', { hotel_block: this.block, name: 'New Room' })
      return this.addRoommates(room)
    },
    async rematchAll(event) {
      this.roomOffset = 0
      this.$confirm.require({
        target: event.currentTarget,
        message: 'This will delete unlocked/incomplete rooms then recreate them. Are you sure?',
        icon: 'pi pi-exclamation-triangle',
        accept: () => {
          this.loading = true
          post('/api/event/' + this.event.id + '/hotel/' + this.block + '/rematch_all', { weights: {} }).then(() => {
            this.fetchRooms()
            this.fetchRequests()
            this.loading = false
          })
        },
        reject: () => {

        }
      })
    },
    async removeRoom(room) {
      this.roomOffset = 0
      await del('/api/event/' + this.event.id + '/hotel_room/' + room.id)
      this.fetchRooms()
      this.fetchRequests()
    },
    async roomInfo(room) {
      this.roomDetails = await get('/api/event/' + this.event.id + '/hotel/room_details', { rooms: room.id })
      this.currentRoom = room
      this.showRoomInfo = true
    },
    async saveInfo(details) {

    },
    async cancelInfo() {
      this.showRoomInfo = false
    },
    async removeRoommate(room, roommate) {
      await post('/api/event/' + this.event.id + '/hotel/' + this.block + '/room/' + room.id + '/remove_roommates', { roommates: [roommate] })
      this.fetchRooms()
      this.fetchRequests()
    },
    async addRoommates(room) {
      const roommates = []
      for (const roommate of this.selectedRequests) {
        roommates.push(roommate.badge)
      }
      await post('/api/event/' + this.event.id + '/hotel/' + this.block + '/room/' + room.id + '/add_roommates', { roommates: roommates })
      this.fetchRooms()
      this.fetchRequests()
    },
    async roomSearch() {
      this.roomOffset = 0
      this.fetchRooms()
    },
    async saveRoom(room) {
      room.edit = false
      try {
        await patch('/api/event/' + this.event.id + '/hotel_room/' + room.id, { id: room.id, completed: room.completed, locked: room.locked, notes: room.notes, name: room.name, messages: room.messages })
        this.$toast.add({ severity: 'success', summary: 'Saved ' + room.name + ' successfully!', life: 500 })
      } catch {
        this.$toast.add({ severity: 'error', summary: 'Failed to save ' + room.name, life: 3000 })
      }
    },
    completeRoom(room, completed) {
      room.completed = completed
      this.saveRoom(room)
      this.fetchRooms()
    },
    lockRoom(room, locked) {
      room.locked = locked
      this.saveRoom(room)
    },
    async clearAutoMatches(evt) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'This will delete unlocked/incomplete rooms. Are you sure?',
        icon: 'pi pi-exclamation-triangle',
        accept: () => {
          this.loading = true
          post('/api/event/' + this.event.id + '/hotel/' + this.block + '/clear_matches', { weights: {} }).then(() => {
            this.fetchRooms()
            this.fetchRequests()
            this.loading = false
          })
        },
        reject: () => {

        }
      })
    },
    async editRequest(request) {
      this.editedRequestID = request.id;
      this.editedRequest = await get('/api/event/' + this.event.id + '/hotel/request/' + request.id);
      this.editingRequest = true;
    },
    async editRequestByBadge(badgeID) {
      const request = await get('/api/event/' + this.event.id + '/hotel_room_request', { badge: badgeID, full: true })
      this.editedRequestID = request[0].id
      this.editedRequest = await get('/api/event/' + this.event.id + '/hotel/request/' + request[0].id);
      this.editingRequest = true;
    },
    saveRequest(request) {
      patch('/api/event/' + this.event.id + '/hotel/request/' + this.editedRequestID, request).then(() => {
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 300 })
        this.editingRequest = false;
        this.fetchRequests()
        this.fetchRooms()
      }).catch(() => {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 300 })
      })
    },
    cancelRequest() {
      this.editingRequest = false;
    }
  },
  watch: {
    event() {
      this.rooms = []
      this.roomNights = []
      get('/api/event/' + this.event.id + '/hotel_room_night', { sort: 'date' }).then((roomNights) => {
        this.roomNights = roomNights
        this.getblocks().then(() => {
          this.load()
        })
      })
    },
    block() {
      this.fetchRequests()
      this.fetchRooms()
    },
    hidecompleted() {
      this.fetchRooms()
    }
  }
}
</script>
