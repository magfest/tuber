<template>
    <div class="card">
        <h3>Logging out...</h3>
    </div>
</template>

<style>
</style>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'
import { AppActionTypes } from '../store/modules/app/actions'

@Options({
  name: 'Login',
  components: {
  },
  data: () => ({
  }),
  mounted () {
    this.$store.dispatch(AppActionTypes.LOGOUT)
  }
})
export default class Login extends Vue {}
</script>
