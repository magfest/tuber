<template>
  <b-nav-item-dropdown id="hotels-dropdown" text="Hotels" to="#">
    <b-dropdown-item>Room Request</b-dropdown-item>
    <b-dropdown-item>Approve Requests</b-dropdown-item>
    <b-dropdown-item>Assign Rooms</b-dropdown-item>
    <b-dropdown-item>Settings</b-dropdown-item>
    <b-dropdown-divider></b-dropdown-divider>
    <b-dropdown-header>Reports</b-dropdown-header>
  </b-nav-item-dropdown>
</template>
<script>
  export default {
    name: 'hotel-nav'
  };
</script>
