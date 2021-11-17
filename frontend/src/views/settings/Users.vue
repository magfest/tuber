<template>
  <div class="card">
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <h3>Users</h3>
    <user-table />
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex'

import { UserTable } from '../../components/settings'
export default {
  name: 'UserSettings',
  props: [
    ''
  ],
  components: {
    UserTable
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
