<template>
    <div>
        <tuber-table tableTitle="Hotel Rooms" formTitle="Hotel Room" url="/api/event/<event>/hotel_room"
            :parameters="parameters" :autoload="false" :format="format" ref="table" :filters="filters">

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
                        <div v-for="roommate in slotProps.data.roommates" :key="slotProps.data.id + '_' + roommate.id">
                            {{ roommate.name }}
                            <Chip v-for="error in roommate.errors" :key="roommate.id + error" :label="error" />
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
    </div>
</template>

<style scoped>
.p-chip {
    height: 15px;
    font-size: x-small;
}
</style>

<script>
import RoomDetails from './RoomDetails.vue'
import TuberTable from '../../TuberTable.vue'
import { mapGetters } from 'vuex'
import { get } from '@/lib/rest'
import { FilterMatchMode } from 'primevue/api'

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
      badgeSearch: ''
    }
  },
  components: {
    RoomDetails,
    TuberTable
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
      this.hotelBlocks = await get('/api/event/' + this.event.id + '/hotel_room_block')
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
        room.name = room.name ? room.name : 'Room ' + room.id
        const ID = room.id.toString()
        if (Object.prototype.hasOwnProperty.call(roomDetails, ID)) {
          room.empty_slots = roomDetails[ID].empty_slots
          room.roommates = roomDetails[ID].roommates
        }
      }
      return rooms
    },
    complete (data, completed) {
      this.$refs.table.save({ id: data.id, completed: completed })
    },
    lockRoom (data, locked) {
      this.$refs.table.save({ id: data.id, locked: locked })
    }
  },
  watch: {
    event () {
      this.load()
    }
  }
}
</script>
