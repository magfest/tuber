<template>
  <div class="container">
    <div class="d-flex justify-center">
      <h2>My Shifts</h2>
    </div>
    <div v-if="!loading && shifts.length === 0" class="d-flex justify-center">
      You currently have no shifts scheduled.
    </div>
  </div>
</template>

<script>
  import { mapAsyncDump } from '../../mixins/rest';
  export default {
    name: 'Shifts',

    data(){
      return {
        loading: false
      }
    },

    asyncComputed: {
      ...mapAsyncDump([
        'shifts'
      ])
    }
  };
</script>

<style scoped>

</style>
