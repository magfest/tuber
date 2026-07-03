<template>
  <a class="detail-link" href="#" @click.prevent="open">
    <i class="pi pi-home mr-1" style="font-size: 0.85em" />{{ name || ('Room #' + roomId) }}
  </a>
</template>

<style scoped>
.detail-link {
  color: var(--primary-color, #2196f3);
  text-decoration: none;
  cursor: pointer;
}
.detail-link:hover {
  text-decoration: underline;
}
</style>

<script>
import { openRoom } from '../../../lib/detailModals'

export default {
  name: 'RoomName',
  props: [
    'roomId',
    'name'
  ],
  methods: {
    open () {
      openRoom(this.$router, this.$route, this.roomId)
    }
  }
}
</script>
