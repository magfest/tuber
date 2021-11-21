<template>
    <div>
    <DataTable ref="dt" :value="formattedRooms" :loading="loading" :paginator="true" :rows="25" class="p-datatable-sm"
    :lazy="true" :totalRecords="totalRooms" @page="onPage($event)" @sort="onSort($event)">
        <Column field="name" header="Name" :sortable="true">
            <template #body="slotProps">
                {{ slotProps.data.name ? slotProps.data.name : "Room " + slotProps.data.id }}
            </template>
        </Column>
        <Column field="empty_slots" header="Empty Slots" style="width: 5rem"></Column>
        <Column field="roommates" header="Roommates">
            <template #body="slotProps">
                <div v-for="roommate in slotProps.data.roommates" :key="slotProps.data.id + '_' + roommate.id">
                    {{ badgeLookup[roommate.id].public_name }}
                    <Chip v-for="error in roommate.errors" :key="roommate.id + error" :label="errorMessages[error]" />
                </div>
            </template>
        </Column>
        <Column field="notes" header="Internal Notes" :sortable="true"></Column>
        <Column header="Actions" style="width: 10rem">
            <template #body="slotProps">
                <Button v-if="slotProps.data.completed" class="p-button-success mr-2" icon="pi pi-check-circle" @click="complete(slotProps.data, false)" />
                  <Button v-else class="p-button-warning mr-2" icon="pi pi-circle-off" @click="complete(slotProps.data, true)" />
                <Button @click="edit(slotProps.data)" icon="pi pi-cog" class="p-button-info ml-2" />
            </template>
        </Column>
        </DataTable>

        <Dialog v-model:visible="editing">
            <template #header>
                <h3>Hotel Room</h3>
            </template>

            <room-details :id="edited" ref="form" />

            <template #footer>
                <Button label="Cancel" @click="cancel" icon="pi pi-times" class="p-button-text"/>
                <Button label="Save" @click="save" icon="pi pi-check" autofocus />
            </template>
        </Dialog>
    </div>
</template>

<style scoped>
.p-chip {
    height: 15px;
    font-size: x-small;
}
</style>

<script>
import { mapGetters } from 'vuex'
import { get, patch } from '@/lib/rest'
import RoomDetails from './RoomDetails.vue'
import { ModelActionTypes } from '@/store/modules/models/actions'

export default {
  name: 'RoomTable',
  props: [
    'hotelBlock',
    'hideCompleted'
  ],
  components: {
    RoomDetails
  },
  data: () => ({
    hotelRooms: [],
    hotelRoomLookup: {},
    editing: false,
    edited: null,
    loading: false,
    roomDetails: {},
    errorMessages: {
      requests_met: 'Missed Roommate',
      nights_match: "Nights Don't Match",
      antirequests_met: 'Roomed with Antirequest'
    },
    lazyParams: {
      first: 0,
      rows: 0,
      sortField: 'name',
      sortOrder: 1,
      filters: {}
    },
    totalRooms: 0
  }),
  computed: {
    ...mapGetters([
      'event',
      'badgeLookup'
    ]),
    formattedRooms () {
      const rooms = []
      for (const hotelRoom of this.hotelRooms) {
        const room = {
          id: hotelRoom.id,
          name: hotelRoom.name ? hotelRoom.name : 'Room ' + hotelRoom.id,
          messages: hotelRoom.messages,
          notes: hotelRoom.notes,
          completed: hotelRoom.completed,
          empty_slots: 0,
          roommates: []
        }
        if (Object.prototype.hasOwnProperty.call(this.roomDetails, hotelRoom.id.toString())) {
          room.empty_slots = this.roomDetails[hotelRoom.id.toString()].empty_slots
          for (const roommate of hotelRoom.roommates) {
            const roommateDetail = {
              id: roommate,
              name: this.badgeLookup[roommate].public_name,
              errors: []
            }
            for (const [key, value] of Object.entries(this.roomDetails[hotelRoom.id.toString()].roommates[roommate.toString()])) {
              if (!value) {
                roommateDetail.errors.push(key)
              }
            }
            room.roommates.push(roommateDetail)
          }
        }
        rooms.push(room)
      }
      return rooms
    }
  },
  mounted () {
    this.lazyParams.rows = this.$refs.dt.rows
  },
  methods: {
    async load () {
      this.loading = true
      await this.$store.dispatch(ModelActionTypes.LOAD_BADGES)
      if (this.hotelBlock) {
        if (this.hideCompleted) {
          this.hotelRooms = await get('/api/event/' + this.event.id + '/hotel_room', {
            full: true,
            hotel_block: this.hotelBlock,
            completed: true,
            offset: this.lazyParams.first,
            limit: this.lazyParams.rows,
            sort: this.lazyParams.sortField,
            order: this.lazyParams.sortOrder > 0 ? 'asc' : 'desc'
          })
          this.totalRooms = await get('/api/event/' + this.event.id + '/hotel_room', { count: true, completed: true, hotel_block: this.hotelBlock })
        } else {
          this.hotelRooms = await get('/api/event/' + this.event.id + '/hotel_room', {
            full: true,
            hotel_block: this.hotelBlock,
            offset: this.lazyParams.first,
            limit: this.lazyParams.rows,
            sort: this.lazyParams.sortField,
            order: this.lazyParams.sortOrder > 0 ? 'asc' : 'desc'
          })
          this.totalRooms = await get('/api/event/' + this.event.id + '/hotel_room', { count: true, hotel_block: this.hotelBlock })
        }
        this.hotelRoomLookup = {}
        for (const room of this.hotelRooms) {
          this.hotelRoomLookup[room.id] = room
        }
      }
      const roomIDs = []
      for (const room of this.hotelRooms) {
        roomIDs.push(room.id)
      }
      if (roomIDs) {
        this.roomDetails = await get('/api/event/' + this.event.id + '/hotel/room_details', { rooms: roomIDs })
      }
      this.loading = false
    },
    edit (data) {
      this.edited = data.id
      this.editing = true
    },
    cancel () {
      this.editing = false
      this.edited = null
    },
    save () {
      this.$refs.form.save().then(() => {
        this.editing = false
        this.edited = null
        this.load()
      })
    },
    complete (data, completed) {
      this.hotelRoomLookup[data.id].completed = completed
      patch('/api/event/' + this.event.id + '/hotel_room/' + data.id, { completed: completed }).then(() => {
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 300 })
      }).catch(() => {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 300 })
      })
    },
    onPage (event) {
      this.lazyParams = event
      this.load()
    },
    onSort (event) {
      this.lazyParams = event
      this.load()
    }
  },
  watch: {
    event () {
      this.load()
    },
    hotelBlock () {
      this.load()
    },
    hideCompleted () {
      this.load()
    }
  }
}
</script>
