<template>
  <div class="card">
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <h3>Room Settings</h3>
    <TabView>
        <TabPanel header="Room Blocks">
            Room blocks allow people to be divided into groups that will be independently matched into rooms.
            <room-block-table />
        </TabPanel>
        <TabPanel header="Locations">
            Rooms can be grouped into locations based on which hotel they will be in.
            <location-table />
        </TabPanel>
        <TabPanel header="Room Nights">
            Room nights are the dates that can be requested for this event.
            <room-night-table />
        </TabPanel>
    </TabView>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex'

import { RoomBlockTable, LocationTable, RoomNightTable } from '../../components/rooming'
export default {
  name: 'RoomSettings',
  props: [
    ''
  ],
  components: {
    RoomBlockTable,
    LocationTable,
    RoomNightTable
  },
  data: () => ({
  }),
  computed: {
    ...mapGetters([
      'event'
    ])
  },
  mounted () {
  },
  methods: {
  },
  watch: {
  }
}
</script>
