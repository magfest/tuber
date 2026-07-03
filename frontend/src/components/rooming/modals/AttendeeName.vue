<template>
  <a class="detail-link" href="#" @click.prevent="open">{{ name || ('#' + badgeId) }}</a>
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
import { openAttendee } from '../../../lib/detailModals'

export default {
  name: 'AttendeeName',
  props: [
    'badgeId',
    'name'
  ],
  methods: {
    open () {
      openAttendee(this.$router, this.$route, this.badgeId)
    }
  }
}
</script>
