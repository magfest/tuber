<template>
    <div class="card">
        <Toast />
        <h3>Logging out...</h3>
    </div>
</template>

<style>
</style>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'
import { AppActionTypes } from '../store/modules/app/actions'

export default {
  name: 'Login',
  components: {
  },
  data: () => ({
  }),
  mounted () {
    this.$store.dispatch(AppActionTypes.LOGOUT).then(() => {
      this.$router.push('/')
    }).catch(() => {
      this.$toast.add({ severity: 'error', summary: 'Failed to Log Out', detail: 'Could not terminate user session. Are you online?' })
    })
  }
}
</script>
