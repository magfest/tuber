<template>
    <form @submit.prevent>
        <div class="field">
            <label for="name">Name</label><br>
            <InputText id="name" v-model="hotelRoomBlock.name" /><br>
          </div><br>

          <div class="field">
            <label for="description">Description</label><br>
            <InputText id="description" v-model="hotelRoomBlock.description" /><br>
          </div><br>
    </form>
</template>

<script>
import { mapGetters } from 'vuex'
import { get, post, patch } from '@/lib/rest'

export default {
  name: 'RoomBlockForm',
  props: [
    'id'
  ],
  components: {
  },
  data: () => ({
    hotelRoomBlock: {
      name: '',
      description: ''
    }
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    url () {
      if (this.id) {
        return '/api/event/' + this.event.id + '/hotel_room_block/' + this.id
      }
      return '/api/event/' + this.event.id + '/hotel_room_block'
    }
  },
  mounted () {
    this.load()
  },
  methods: {
    load () {
      if (this.id) {
        get(this.url, { sort: 'name' }).then((hotelRoomBlock) => {
          this.hotelRoomBlock = hotelRoomBlock
        })
      }
    },
    save () {
      if (this.id) {
        return patch(this.url, this.hotelRoomBlock).then(() => {
          this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 300 })
        }).catch(() => {
          this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 300 })
        })
      } else {
        return post(this.url, this.hotelRoomBlock).then(() => {
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
