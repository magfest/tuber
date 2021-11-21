<template>
  <div class="card">
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <h3>Rooms</h3>
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
    <room-table :hotelBlock="hotelBlock" :hideCompleted="hideCompleted" />
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex'
import { RoomTable } from '../../components/rooming'
import { get } from '@/lib/rest'

export default {
  name: 'Rooms',
  props: [
    ''
  ],
  components: {
    RoomTable
  },
  data: () => ({
    hotelBlocks: [],
    hotelBlock: null,
    hideCompleted: false
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
    async load () {
      this.hotelBlocks = await get('/api/event/' + this.event.id + '/hotel_room_block')
      if (this.hotelBlocks && !this.hotelBlock) {
        this.hotelBlock = this.hotelBlocks[0].id
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
