<template>
    <div>
        <tuber-table tableTitle="Hotel Rooms" formTitle="Hotel Room" url="/api/event/<event>/hotel_room"
            :parameters="parameters" :autoload="false" :format="format" ref="table" :filters="filters" :neverload="neverload">

            <template #controls>
                <div class="grid">
                    <div class="col">
                        <Dropdown :options="hotelBlocks" optionLabel="name" optionValue="id" v-model="hotelBlock" />
                    </div>
                    <div class="col">
                        <span class="field-checkbox">
                            <Checkbox id="hideCompleted" v-model="hideCompleted" :binary="true" />
                            <label for="hideCompleted">Hide Completed</label>
                        </span>
                    </div>
                </div>
            </template>

            <template #columns>
                <Column field="name" header="Name" filterField="name" style="width: 10rem" :sortable="true">
                    <template #body="slotProps">
                        {{ slotProps.data.name ? slotProps.data.name : "Room " + slotProps.data.id }}
                    </template>
                    <template #filter="{filterModel,filterCallback}">
                        <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" :placeholder="`Search by name`" v-tooltip.top.focus="'Hit enter key to filter'"/>
                    </template>
                </Column>
                <Column field="empty_slots" header="Empty Slots" style="width: 5rem"></Column>
                <Column field="roommates" header="Roommates" :showFilterMatchModes="false">
                    <template #body="slotProps">
                      <div>
                        <div v-for="group in slotProps.data.groups" :key="Object.keys(group)[0] + '_group'" class="roommate_group">
                          <div v-for="roommate in group" :key="slotProps.data.id + '_' + roommate.id">
                              <Button class="p-button-info minibutton" icon="pi pi-plus" iconPos="right" @click="viewRequest(roommate.id)" />
                              {{ roommate.name }}
                              <Chip v-for="error in roommate.errors" :key="roommate.id + error" :label="error" />
                          </div>
                        </div>
                      </div>
                    </template>
                    <template #filter="{filterModel,filterCallback}">
                        <InputText type="text" v-model="badgeSearch" @keydown.enter="loadBadges(filterModel, filterCallback)" class="p-column-filter" :placeholder="`Search by name`" v-tooltip.top.focus="'Hit enter key to filter'"/>
                    </template>
                </Column>
                <Column field="notes" header="Internal Notes" :sortable="true"></Column>
            </template>

            <template #actions="tableProps">
                <Column header="Actions" style="width: 15rem">
                    <template #body="slotProps">
                        <Button v-if="slotProps.data.completed" class="p-button-success" icon="pi pi-check-circle" @click="complete(slotProps.data, false)" />
                        <Button v-else class="p-button-warning" icon="pi pi-circle-off" @click="complete(slotProps.data, true)" />
                        <Button v-if="slotProps.data.locked" class="p-button-success ml-2" icon="pi pi-lock" @click="lockRoom(slotProps.data, false)" />
                        <Button v-else class="p-button-warning ml-2" icon="pi pi-unlock" @click="lockRoom(slotProps.data, true)" />
                        <Button @click="tableProps.edit(slotProps.data)" icon="pi pi-cog" class="p-button-info ml-2" />
                        <Button @click="tableProps.remove($event, slotProps.data)" icon="pi pi-times" class="p-button-danger ml-2" />
                    </template>
                </Column>
            </template>

            <template #form="props">
                <room-details :modelValue="props.modelValue" />
            </template>
        </tuber-table>

        <Dialog v-model:visible="requestFormActive">
            <template #header>
                <h3>Room Request</h3>
            </template>

            <request-short-form :modelValue="roomRequest" />

            <template #footer>
                <Button label="Cancel" @click="cancel" icon="pi pi-times" class="p-button-text"/>
                <Button label="Save" @click="saveRequest(edited)" icon="pi pi-check" autofocus />
            </template>
        </Dialog>
    </div>
</template>

<style scoped>
.p-chip {
    height: 15px;
    font-size: x-small;
}
.p-button.p-button-icon-only.minibutton {
  padding-top: 0;
  padding-bottom: 0;
  width: 19px;
  margin-bottom: 2px;
  margin-right: 2px;
}

.roommate_group {
  margin-bottom: 5px;
}
.roommate_group:nth-child(1) {
  background: darkred;
}
.roommate_group:nth-child(2) {
  background: darkblue;
}
.roommate_group:nth-child(3) {
  background: darkgreen;
}
.roommate_group:nth-child(4) {
  background: brown;
}
</style>

<script>
import RoomDetails from './RoomDetails.vue'
import TuberTable from '../../TuberTable.vue'
import { mapGetters } from 'vuex'
import { get, patch } from '@/lib/rest'
import { FilterMatchMode } from 'primevue/api'
import RequestShortForm from '../requests/RequestShortForm.vue'

export default {
  name: 'RoomTable',
  data () {
    return {
      hideCompleted: false,
      hotelBlocks: [],
      hotelBlock: null,
      filters: {
        name: { value: null, matchMode: FilterMatchMode.CONTAINS },
        roommates: { value: null, matchMode: FilterMatchMode.CONTAINS }
      },
      badgeSearch: '',
      roomRequest: {},
      requestFormActive: false,
      roomNights: [],
      neverload: true
    }
  },
  components: {
    RoomDetails,
    TuberTable,
    RequestShortForm
  },
  computed: {
    ...mapGetters([
      'event'
    ]),
    parameters () {
      const params = {
        full: true
      }
      if (this.hotelBlock) {
        params.hotel_block = this.hotelBlock
      }
      if (this.hideCompleted) {
        params.completed = false
      }
      return params
    }
  },
  mounted () {
    this.load()
  },
  methods: {
    async load () {
      if (!this.event) {
        return
      }
      this.hotelBlocks = await get('/api/event/' + this.event.id + '/hotel_room_block', { sort: 'name' })
      this.neverload = false
      if (this.hotelBlocks && !this.hotelBlocks.includes(this.hotelBlock)) {
        this.hotelBlock = this.hotelBlocks[0].id
      }
    },
    async loadBadges (filterModel, filterCallback) {
      if (this.badgeSearch) {
        const badges = await get('/api/event/' + this.event.id + '/badge', { search: this.badgeSearch, search_field: 'public_name' })
        const badgeIDs = []
        for (const badge of badges) {
          badgeIDs.push(badge.id)
        }
        filterModel.value = badgeIDs
      } else {
        filterModel.value = null
      }

      filterCallback()
    },
    async format (rooms) {
      const roomIDs = []
      let roomDetails = {}
      for (const room of rooms) {
        roomIDs.push(room.id)
      }
      roomDetails = await get('/api/event/' + this.event.id + '/hotel/room_details', { rooms: roomIDs })
      for (const room of rooms) {
        room.empty_slots = 0
        room.roommates = []
        room.groups = []
        room.name = room.name ? room.name : 'Room ' + room.id
        const ID = room.id.toString()
        if (Object.prototype.hasOwnProperty.call(roomDetails, ID)) {
          room.empty_slots = roomDetails[ID].empty_slots
          room.roommates = roomDetails[ID].roommates
          room.groups = roomDetails[ID].groups
        }
      }
      return rooms
    },
    complete (data, completed) {
      this.$refs.table.save({ id: data.id, completed: completed })
    },
    lockRoom (data, locked) {
      this.$refs.table.save({ id: data.id, locked: locked })
    },
    async viewRequest (requestID) {
      let request = await get('/api/event/' + this.event.id + '/hotel_room_request', { badge: requestID, full: true, deep: true })
      request = request[0]
      this.roomNights = await get('/api/event/' + this.event.id + '/hotel_room_night', { sort: 'date' })
      request.room_nights = []
      request.nights = {}
      for (const rn of this.roomNights) {
        const night = {
          name: rn.name,
          id: rn.id
        }
        let requested = false
        for (const nightreq of request.room_night_requests) {
          if (nightreq.room_night === rn.id && nightreq.requested) {
            requested = true
            break
          }
        }
        if (rn.restricted) {
          for (const nightapp of request.room_night_approvals) {
            if (nightapp.room_night === rn.id && nightapp.approved) {
              night.approved = true
              break
            }
          }
        } else {
          night.approved = requested
        }
        night.requested = requested
        request.nights[rn.id] = requested
        request.room_nights.push(night)
      }
      this.roomRequest = request
      this.requestFormActive = true
    },
    cancel () {
      this.requestFormActive = false
      this.roomRequest = {}
    },
    async saveRequest () {
      try {
        this.roomRequest.requested_roommates = []
        for (const roommate of this.roomRequest.roommate_requests) {
          this.roomRequest.requested_roommates.push(roommate.id)
        }
        this.roomRequest.antirequested_roommates = []
        for (const roommate of this.roomRequest.roommate_anti_requests) {
          this.roomRequest.antirequested_roommates.push(roommate.id)
        }
        await patch('/api/event/' + this.event.id + '/hotel/request/' + this.roomRequest.id, this.roomRequest)
        this.cancel()
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', detail: 'Your request has been saved. You may continue editing it until the deadline.', life: 3000 })
      } catch (error) {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 3000 })
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
