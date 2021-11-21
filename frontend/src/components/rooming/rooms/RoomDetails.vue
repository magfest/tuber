<template>
    <form @submit.prevent>
        <div class="field">
            <label for="name">Name</label><br>
            <InputText id="name" v-model="hotelRoom.name" /><br>
          </div><br>

          <div class="field">
            <label for="messages">Messages</label><br>
            <Textarea id="messages" v-model="hotelRoom.messages" /><br>
          </div><br>

          <div class="field">
            <label for="notes">Notes</label><br>
            <Textarea id="notes" v-model="hotelRoom.notes" /><br>
          </div><br>
    </form>
</template>

<script>
import { mapGetters } from 'vuex'
import { get, post, patch } from '@/lib/rest'

export default {
  name: 'RoomDetails',
  props: [
    'id'
  ],
  components: {
  },
  data: () => ({
    hotelRoom: {
      name: '',
      messages: '',
      notes: ''
    }
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    url () {
      if (this.id) {
        return '/api/event/' + this.event.id + '/hotel_room/' + this.id
      }
      return '/api/event/' + this.event.id + '/hotel_room'
    }
  },
  mounted () {
    this.load()
  },
  methods: {
    load () {
      if (this.id) {
        get(this.url).then((hotelRoom) => {
          this.hotelRoom = hotelRoom
        })
      }
    },
    save () {
      if (this.id) {
        return patch(this.url, this.hotelRoom).then(() => {
          this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 300 })
        }).catch(() => {
          this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 300 })
        })
      } else {
        return post(this.url, this.hotelRoom).then(() => {
          this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 300 })
        }).catch(() => {
          this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 300 })
        })
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
