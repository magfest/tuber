<template>
    <form @submit.prevent>
      <div class="grid">
        <div class="field col">
          <label for="name">Name</label><br>
          <InputText id="name" v-model="data.name" /><br>
        </div>

        <div class="field col">
          <label for="messages">Messages</label><br>
          <Textarea id="messages" v-model="data.messages" /><br>
        </div>

        <div class="field col">
          <label for="notes">Notes</label><br>
          <Textarea id="notes" v-model="data.notes" /><br>
        </div><br>
      </div>
      <table>
        <tr>
          <th>Name</th>
          <th>Room Nights</th>
          <th>Warnings</th>
        </tr>
        <tr>
          <td></td>
          <td>
            <Tag  v-for="night in roomNights" :key="'r'+night.id" :value="night.name.slice(0,2)" :severity="details.room_nights.includes(night.id) ? 'primary': 'danger'" class="mr-1" style="width: 22px" />
          </td>
          <td></td>
        </tr>
        <tr v-for="roommate in Object.values(details.roommates)" :key="roommate.id">
          <td>
            <Button class="p-button-danger minibutton" icon="pi pi-times" iconPos="right" @click="removeRoommate(roommate)" />
            {{ roommate.name}}</td>
          <td>
            <Tag @click="toggleAssignment(roommate, night)" v-for="night in roomNights" :key="'rn'+night.id+roommate.id" :value="night.name.slice(0,2)" :severity="roommate.room_night_assignments.hasOwnProperty(night.id) ? 'primary': 'danger'" class="mr-1" style="width: 22px" />
          </td>
          <td>
            <Chip v-for="error in roommate.errors" :key="roommate.id + error" :label="error" />
          </td>
        </tr>
      </table>
      <h4>Add Roommates</h4>
      <InputText class="mt-2" placeholder="Name Search" id="search" v-model="search"></InputText>
      <table>
        <tr>
          <th>Name</th>
          <th>Needed Room Nights</th>
        </tr>
        <tr v-for="roommate in matches" :key="roommate.id">
          <td><Button class="minibutton" icon="pi pi-plus" iconPos="right" @click="addRoommate(roommate)" />{{ roommate.name }}</td>
          <td>
            <Tag  v-for="night in roomNights" :key="'rnr'+night.id+roommate.id" :value="night.name.slice(0,2)" :severity="roommate.missing_nights.includes(night.id) ? 'primary':  'danger'" class="mr-1" style="width: 22px" />
          </td>
        </tr>
      </table>
    </form>
</template>

<script>
import { get, post, del } from '@/lib/rest'
import { mapGetters } from 'vuex'

export default {
  name: 'RoomDetails',
  props: [
    'modelValue'
  ],
  computed: {
    ...mapGetters([
      'event'
    ])
  },
  data () {
    return {
      data: this.modelValue,
      details: {
        roommates: {}
      },
      roomNights: [],
      search: '',
      matches: []
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
      const resp = await get('/api/event/' + this.event.id + '/hotel/room_details', { rooms: [this.data.id] })

      this.details = resp[this.data.id.toString()]
      this.roomNights = await get('/api/event/' + this.event.id + '/hotel_room_night', { sort: 'date' })
      await this.matchingRoomates()
    },
    async toggleAssignment (roommate, night) {
      if (Object.prototype.hasOwnProperty.call(roommate.room_night_assignments, night.id)) {
        try {
          await del('/api/event/' + this.event.id + '/room_night_assignment/' + roommate.room_night_assignments[night.id])
          await this.load()
          this.$toast.add({ severity: 'success', summary: roommate.name + ' removed from ' + night.name + ' successfully', life: 3000 })
        } catch (error) {
          this.$toast.add({ severity: 'error', summary: 'Failed to remove room assignment', life: 3000 })
        }
      } else {
        try {
          await post('/api/event/' + this.event.id + '/room_night_assignment', {
            event: this.event.id,
            badge: roommate.id,
            room_night: night.id,
            hotel_room: this.data.id
          })
          await this.load()
          this.$toast.add({ severity: 'success', summary: roommate.name + ' assigned on ' + night.name + ' successfully', life: 3000 })
        } catch (error) {
          this.$toast.add({ severity: 'error', summary: 'Failed to add room assignment', life: 3000 })
        }
      }
    },
    async addRoommate (roommate) {
      try {
        await post('/api/event/' + this.event.id + '/hotel/' + this.data.hotel_block + '/room/' + this.data.id + '/add_roommates', { roommates: [roommate.id] })
        this.$toast.add({ severity: 'success', summary: roommate.name + ' added', life: 3000 })
        await this.load()
      } catch (error) {
        this.$toast.add({ severity: 'error', summary: 'Failed to add ' + roommate.name, life: 3000 })
      }
    },
    async removeRoommate (roommate) {
      try {
        await post('/api/event/' + this.event.id + '/hotel/' + this.data.hotel_block + '/room/' + this.data.id + '/remove_roommates', { roommates: [roommate.id] })
        this.$toast.add({ severity: 'success', summary: roommate.name + ' removed', life: 3000 })
        await this.load()
      } catch (error) {
        this.$toast.add({ severity: 'error', summary: 'Failed to remove ' + roommate.name, life: 3000 })
      }
    },
    async matchingRoomates () {
      try {
        if (this.search) {
          this.matches = await get('/api/event/' + this.event.id + '/hotel/matching_roommates', { search: this.search, hotel_room: this.data.id })
        } else {
          this.matches = await get('/api/event/' + this.event.id + '/hotel/matching_roommates', { hotel_room: this.data.id })
        }
      } catch {
        this.$toast.add({ severity: 'error', summary: 'Failed to get matching roommates', life: 3000 })
      }
    }
  },
  watch: {
    search () {
      this.matchingRoomates()
    }
  }
}
</script>
