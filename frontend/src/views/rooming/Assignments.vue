<template>
  <div class="card">
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <h3>Room Assignments</h3>
    <Toolbar class="mb-1">
        <template #left>
            <Button class="p-button-success mr-2" @click="createRoom"><u>C</u>reate Room</Button>
            <Button class="p-button-info mr-2" @click="rematchAll($event)"><u>R</u>ematch All</Button>
        </template>

        <template #right>
            <label for="blockselect" class="mr-2">Room Block</label>
            <Dropdown id="blockselect" :options="blocks" v-model="block" optionLabel="name" optionValue="id" />
        </template>
    </Toolbar>

    <div class="grid">
      <div class="col">
        <DataTable class="p-datatable-sm" ref="dt" :lazy="true" selectionMode="multiple" :value="filteredRequests" :paginator="true" :rows="10" dataKey="id"
         v-model:filters="requestFilters" filterDisplay="row" :globalFilterFields="['public_name']" v-model:selection="selectedRequests"
         :totalRecords="totalRequests" :loading="loading" @page="onPage($event)" @sort="onSort($event)" @filter="onFilter($event)">
          <Column header="Name" field="first_name" filterField="first_name" style="width: 8rem" :sortable="true">
            <template #body="slotProps">
              {{ badgeLookup[slotProps.data.badge] != undefined ? badgeLookup[slotProps.data.badge].public_name : "loading" }}
            </template>
          </Column>
          <Column style="width: 2rem" v-for="night in roomNights" :key="'rn'+night.id">
            <template #body="slotProps">
              <Tag :value="night.name.slice(0,2)" :severity="slotProps.data.nights[night.id] ? 'primary': (slotProps.data.nights_requested[night.id] ? 'warning' : 'danger')" class="mr-1" style="width: 27px" />
            </template>
          </Column>
          <Column header="Notes" field="notes" filterField="notes" :sortable="true">
            <template #filter="{filterModel,filterCallback}">
                <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" :placeholder="`Search Requests by Name`" v-tooltip.top.focus="'Hit enter key to filter'"/>
            </template>
          </Column>
        </DataTable>
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
        <Card v-for="room in filteredRooms" :key="'rm'+room.id" class="mb-2">
            <template #title>
              <div class="flex justify-content-between">
                <span>
                  <Button v-if="room.completed" class="p-button-success mr-2" icon="pi pi-check-circle" @click="completeRoom(room, false)" />
                  <Button v-else class="p-button-warning mr-2" icon="pi pi-circle-off" @click="completeRoom(room, true)" />
                  <Button v-if="room.locked" class="p-button-success mr-2" icon="pi pi-lock" @click="lockRoom(room, false)" />
                  <Button v-else class="p-button-warning mr-2" icon="pi pi-unlock" @click="lockRoom(room, true)" />
                  <InputText v-if="room.edit" v-model="room.name" @blur="saveRoom(room)" />
                  <span v-else @click="room.edit=true">
                    {{ room.name ? room.name : "Room " + room.id}}
                  </span>
                </span>
                <span>
                  <Button class="p-button-info mr-2" icon="pi pi-info-circle" @click="roomInfo(room)" />
                  <Button class="p-button-danger" @click="removeRoom(room)">Remove</Button>
                </span>
              </div>
            </template>
            <template #content>
              <div class="grid">
                <div class="col">
                  <div v-for="roommate in room.roommates" :key="room.id + '_' + roommate">
                    <Button class="p-button-danger minibutton" icon="pi pi-times" iconPos="right" @click="removeRoommate(room, roommate)" />
                    {{ badgeLookup[roommate].public_name }}
                  </div>
                  <div>
                    <Button class="p-button-success minibutton" icon="pi pi-plus" iconPos="right" @click="addRoommates(room)" />
                  </div>
                </div>
                <div class="col">
                  Messages
                  <Textarea v-model="room.messages" rows="5" @change="saveRoom(room)" />
                </div>
                <div class="col">
                  Internal Notes
                  <Textarea v-model="room.notes" rows="5" @change="saveRoom(room)" />
                </div>
              </div>
            </template>
        </Card>
      </div>
    </div>
  </div>
</template>

<style>
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
import { mapGetters } from 'vuex'
import { get, post, patch, del } from '@/lib/rest'
import { FilterMatchMode } from 'primevue/api'
import { ModelActionTypes } from '@/store/modules/models/actions'

export default {
  name: 'RoomAssignments',
  props: [
    ''
  ],
  components: {
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
      notes: { value: null, matchMode: FilterMatchMode.CONTAINS }
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
    filteredRequests: []
  }),
  computed: {
    ...mapGetters([
      'event',
      'departments'
    ]),
    filteredRooms () {
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
    roomNightLookup () {
      const lookup = {}
      for (const night of this.roomNights) {
        lookup[night.id] = night
      }
      return lookup
    },
    badgeLookup () {
      const lookup = {}
      this.badges.forEach((badge) => {
        lookup[badge.id] = badge
      })
      return lookup
    }
  },
  mounted () {
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
    async getblocks () {
      this.blocks = await get('/api/event/' + this.event.id + '/hotel_room_block', { sort: 'name' })
      if (this.blocks) {
        this.block = this.blocks[0].id
      }
    },
    async load () {
      this.loading = true
      this.badges = await get('/api/event/' + this.event.id + '/badge')
      await this.fetchRooms()
      await this.$store.dispatch(ModelActionTypes.LOAD_DEPARTMENTS)
      this.loading = false
    },
    async fetchRooms () {
      this.loading = true
      try {
        if (this.roomSearchText) {
          this.rooms = await get('/api/event/' + this.event.id + '/hotel/room_search', { search: this.roomSearchText })
        } else {
          if (this.hidecompleted) {
            this.rooms = await get('/api/event/' + this.event.id + '/hotel_room', { full: true, limit: 25, hotel_block: this.block, completed: false })
          } else {
            this.rooms = await get('/api/event/' + this.event.id + '/hotel_room', { full: true, limit: 25, hotel_block: this.block })
          }
        }
      } catch (error) {
        this.rooms = []
      }
      this.loading = false
    },
    async fetchRequests () {
      this.loading = true
      try {
        let requests = []
        if (this.lazyParams.filters.notes.value) {
          const searchRes = await get('/api/event/' + this.event.id + '/hotel/' + this.block + '/request_search', {
            approved: true,
            assigned: false,
            search_term: this.lazyParams.filters.notes.value,
            full: true,
            deep: true,
            offset: this.lazyParams.first,
            limit: this.lazyParams.rows,
            sort: this.lazyParams.sortField,
            order: this.lazyParams.sortOrder > 0 ? 'asc' : 'desc'
          })
          requests = searchRes.requests
          this.totalRequests = searchRes.count
        } else {
          this.totalRequests = await get('/api/event/' + this.event.id + '/hotel_room_request', { approved: true, assigned: false, count: true, hotel_block: this.block })
          requests = await get('/api/event/' + this.event.id + '/hotel_room_request', {
            offset: this.lazyParams.first,
            limit: this.lazyParams.rows,
            full: true,
            deep: true,
            approved: true,
            assigned: false,
            hotel_block: this.block,
            sort: this.lazyParams.sortField,
            order: this.lazyParams.sortOrder > 0 ? 'asc' : 'desc'
          })
        }
        const filtered = []
        for (const req of requests) {
          req.room_nights = []
          req.nights = {}
          req.nights_requested = {}
          for (const rn of this.roomNights) {
            const night = {
              name: rn.name,
              id: rn.id
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
            req.nights[rn.id] = approved
            req.nights_requested[rn.id] = requested
            req.room_nights.push(night)
          }
          filtered.push(req)
        }
        this.filteredRequests = filtered
      } catch (error) {
        this.filteredRequests = []
        this.totalRequests = 0
      }
      this.loading = false
    },
    onPage (event) {
      this.lazyParams = event
      this.fetchRequests()
    },
    onSort (event) {
      this.lazyParams = event
      this.fetchRequests()
    },
    onFilter () {
      this.lazyParams.first = 0
      this.lazyParams.filters = this.requestFilters
      this.fetchRequests()
    },
    async createRoom () {
      const room = await post('/api/event/' + this.event.id + '/hotel_room', { hotel_block: this.block })
      return this.addRoommates(room)
    },
    async rematchAll (event) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'This will delete unlocked rooms. Are you sure?',
        icon: 'pi pi-exclamation-triangle',
        accept: async () => {
          this.loading = true
          await post('/api/event/' + this.event.id + '/hotel/' + this.block + '/rematch_all', { weights: {} })
          this.fetchRooms()
          this.fetchRequests()
          this.loading = false
        },
        reject: () => {

        }
      })
    },
    async removeRoom (room) {
      await del('/api/event/' + this.event.id + '/hotel_room/' + room.id)
      this.fetchRooms()
      this.fetchRequests()
    },
    roomInfo (room) {
      console.log('Getting info', room)
    },
    async removeRoommate (room, roommate) {
      await post('/api/event/' + this.event.id + '/hotel/' + this.block + '/room/' + room.id + '/remove_roommates', { roommates: [roommate] })
      this.fetchRooms()
      this.fetchRequests()
    },
    async addRoommates (room) {
      const roommates = []
      for (const roommate of this.selectedRequests) {
        roommates.push(roommate.badge)
      }
      await post('/api/event/' + this.event.id + '/hotel/' + this.block + '/room/' + room.id + '/add_roommates', { roommates: roommates })
      this.fetchRooms()
      this.fetchRequests()
    },
    async roomSearch () {
      this.fetchRooms()
    },
    async saveRoom (room) {
      room.edit = false
      await patch('/api/event/' + this.event.id + '/hotel_room/' + room.id, { id: room.id, completed: room.completed, locked: room.locked, notes: room.notes, name: room.name, messages: room.messages })
      this.fetchRooms()
    },
    completeRoom (room, completed) {
      room.completed = completed
      this.saveRoom(room)
    },
    lockRoom (room, locked) {
      room.locked = locked
      this.saveRoom(room)
    }
  },
  watch: {
    event () {
      this.rooms = []
      this.roomNights = []
      get('/api/event/' + this.event.id + '/hotel_room_night', { sort: 'date' }).then((roomNights) => {
        this.roomNights = roomNights
        this.getblocks().then(() => {
          this.load()
        })
      })
    },
    block () {
      this.fetchRequests()
      this.fetchRooms()
    },
    hidecompleted () {
      this.fetchRooms()
    }
  }
}
</script>
