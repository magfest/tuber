<template>
  <div>
    <attendee-modal v-if="attendeeId" :visible="true" :badge-id="attendeeId"
                    @update:visible="onClose('attendee', $event)" @changed="bumpVersion" />
    <room-modal v-if="roomId" :visible="true" :room-id="roomId"
                @update:visible="onClose('room', $event)" @changed="bumpVersion" />
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { closeDetail } from '../../../lib/detailModals'
import AttendeeModal from './AttendeeModal.vue'
import RoomModal from './RoomModal.vue'

// Mounted once in App.vue. Watches the global ?attendee= and ?room= query
// params so any page (or a shared link) can open the detail modals. Pages
// that want to refresh after modal edits can watch the vuex-free
// `detailmodal-changed` DOM event on window.
export default {
  name: 'DetailModalHost',
  components: {
    AttendeeModal,
    RoomModal
  },
  computed: {
    ...mapGetters([
      'event',
      'loggedIn'
    ]),
    attendeeId () {
      if (!this.loggedIn || !this.event) {
        return null
      }
      const value = this.$route.query.attendee
      return value ? parseInt(value) : null
    },
    roomId () {
      if (!this.loggedIn || !this.event) {
        return null
      }
      const value = this.$route.query.room
      return value ? parseInt(value) : null
    }
  },
  methods: {
    onClose (key, visible) {
      if (!visible) {
        closeDetail(this.$router, this.$route, key)
      }
    },
    bumpVersion () {
      window.dispatchEvent(new CustomEvent('detailmodal-changed'))
    }
  }
}
</script>
