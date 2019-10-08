<template>
  <div>
    <div>
      <p>Welcome {{ user.username }}! This is the event management system for {{ event.name }}.</p>
    </div>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'Home',
  data() {
    return {
    };
  },
  computed: {
    ...mapGetters([
      'event',
      'user',
    ]),
  },
};
</script>
