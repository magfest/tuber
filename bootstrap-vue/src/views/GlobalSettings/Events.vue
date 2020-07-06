<template>
  <div>
    Events
  </div>
</template>

<script>
  import {mapState} from 'vuex';

  export default {
    name: 'Events',

    computed: {
      ...mapState('events', ['events'])
    }
  };
</script>

<style scoped>

</style>
