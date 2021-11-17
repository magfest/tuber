<template>
  <div class="card">
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <h3>Badges</h3>
    <badge-table />
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex'

import { BadgeTable } from '../../components/event'
export default {
  name: 'Badges',
  props: [
    ''
  ],
  components: {
    BadgeTable
  },
  data: () => ({
  }),
  computed: {
    ...mapGetters([
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
