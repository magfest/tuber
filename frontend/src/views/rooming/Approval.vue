<template>
  <div>
    <Toast />
    <h3>Room Night Approvals for {{ department.name }}</h3>
    <p>
        <TriStateCheckbox /> means the request is pending approval<br>
        <TriStateCheckbox :modelValue="true" /> means the request is approved by this department<br>
        <TriStateCheckbox :modelValue="false" /> means the request is rejected by this department<br>
        Click the checkbox once to approve the night, or click twice to reject it. The <b>All Nights</b> buttons allow you to approve or reject all nights at once.<br>
        Non-restricted nights are approved by default.
    </p><br>
    <DataTable :value="requests">
        <Column headerStyle="width: 10em" field="name" header="Name" key="name"></Column>
        <Column headerStyle="width: 3em; transform: rotate(-45deg)" v-for="roomNight of roomNights" :key="roomNight.id" field="room_nights" :header="roomNight.name">
            <template v-if="roomNight.restricted" #body="slotProps">
                <TriStateCheckbox @change="approve(slotProps.data, roomNight.id)" v-if="Object.prototype.hasOwnProperty.call(slotProps.data.room_nights, String(roomNight.id)) && slotProps.data.room_nights[roomNight.id].requested" v-model="slotProps.data.room_nights[String(roomNight.id)].approved" />
            </template>
            <template v-else #body="slotProps">
                <i class="pi pi-check" v-if="Object.prototype.hasOwnProperty.call(slotProps.data.room_nights, String(roomNight.id)) && slotProps.data.room_nights[roomNight.id].requested" />
            </template>
        </Column>
        <Column headerStyle="width: 8em" header="All Nights" key="allnights">
            <template #body="slotProps">
                <Button @click="approveAll(slotProps.data)" icon="pi pi-check" class="p-button-rounded" />
                <Button @click="rejectAll(slotProps.data)" icon="pi pi-times" class="p-button-rounded p-button-danger" />
            </template>
        </Column>
        <Column field="justification" header="Justification" key="justification"></Column>
    </DataTable>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex'
import { get, post } from '@/lib/rest'

export default {
  name: 'RoomApproval',
  props: [
    'departmentID'
  ],
  components: {
  },
  data: () => ({
    department: {},
    requests: [],
    roomNights: []
  }),
  computed: {
    ...mapGetters([
      'event'
    ])
  },
  mounted () {
    if (this.event) {
      this.load()
    }
  },
  methods: {
    load () {
      get('/api/event/' + this.event.id + '/department', { id: this.departmentID }).then((department) => {
        this.department = department[0]
      })
      get('/api/event/' + this.event.id + '/hotel_room_night').then((roomNights) => {
        this.roomNights = roomNights
        get('/api/event/' + this.event.id + '/hotel/requests/' + this.departmentID).then((requests) => {
          this.requests = requests
        })
      })
    },
    approve (request, roomNight) {
      post('/api/event/' + this.event.id + '/hotel/approve/' + this.departmentID, {
        room_night: roomNight,
        badge: request.id,
        approved: request.room_nights[roomNight].approved
      }).then(() => {
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', detail: request.name, life: 300 })
      }).catch(() => {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: request.name })
      })
    },
    approveAll (request) {
      const requests = []
      for (const [roomNight] of Object.entries(request.room_nights)) {
        request.room_nights[roomNight].approved = true
        requests.push(post('/api/event/' + this.event.id + '/hotel/approve/' + this.departmentID, {
          room_night: roomNight,
          badge: request.id,
          approved: true
        }))
      }
      Promise.all(requests).then(() => {
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', detail: request.name, life: 300 })
      }).catch(() => {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: request.name })
      })
    },
    rejectAll (request) {
      const requests = []
      for (const [roomNight] of Object.entries(request.room_nights)) {
        request.room_nights[roomNight].approved = false
        requests.push(post('/api/event/' + this.event.id + '/hotel/approve/' + this.departmentID, {
          room_night: roomNight,
          badge: request.id,
          approved: false
        }))
      }
      Promise.all(requests).then(() => {
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', detail: request.name, life: 300 })
      }).catch(() => {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: request.name })
      })
    }
  },
  watch: {
    event () {
      this.load()
    },
    departmentID () {
      this.load()
    }
  }
}
</script>
