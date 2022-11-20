<template>
  <div class="card">
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <event-table />
  </div>
</template>

<style>

</style>

<script>
import { EventTable } from '../../components/event'
export default {
  name: 'Events',
  components: {
    EventTable
  }
}
</script>
