<template>
  <b-nav-item-dropdown id="hotels-dropdown" text="Hotels" to="#">
    <b-dropdown-item>Room Request</b-dropdown-item>
    <b-dropdown-item>Approve Requests</b-dropdown-item>
    <b-dropdown-item>Assign Rooms</b-dropdown-item>
    <b-dropdown-item>Settings</b-dropdown-item>
  </b-nav-item-dropdown>
</template>
<script>
  export default {
    name: 'hotel-nav'
  };
</script>
