<template>
  <div class="card">
    <Toast />
    <h3>All Room Requests</h3>
    <request-table />
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex'
import { RequestTable } from '../../components/rooming'

export default {
  name: 'RoomRequests',
  components: {
    RequestTable
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
