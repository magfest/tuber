<template>
  <div class="card">
    <Toast />
    <h3>Room Blocking</h3>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex'
import { get, post } from '@/lib/rest'

export default {
  name: 'RoomBlocks',
  props: [
    ''
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
    this.load()
  },
  methods: {
    load () {
      get('/api/event/' + this.event.id + '/department', { id: this.$route.params.departmentID }).then((department) => {
        this.department = department[0]
      })
      get('/api/event/' + this.event.id + '/hotel_room_night').then((roomNights) => {
        this.roomNights = roomNights
        get('/api/event/' + this.event.id + '/hotel/requests/' + this.$route.params.departmentID).then((requests) => {
          this.requests = requests
        })
      })
    },
    approve (request, roomNight) {
      post('/api/event/' + this.event.id + '/hotel/approve/' + this.$route.params.departmentID, {
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
        requests.push(post('/api/event/' + this.event.id + '/hotel/approve/' + this.$route.params.departmentID, {
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
        requests.push(post('/api/event/' + this.event.id + '/hotel/approve/' + this.$route.params.departmentID, {
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
    $route () {
      this.load()
    }
  }
}
</script>
