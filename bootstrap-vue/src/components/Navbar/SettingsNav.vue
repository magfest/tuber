<template>
  <b-nav-item-dropdown id="settings-dropdown" to="#" text="settings">
    <b-dropdown-header>Event</b-dropdown-header>
    <b-dropdown-item>Email Settings</b-dropdown-item>
    <b-dropdown-item>Email Source Settings</b-dropdown-item>
    <b-dropdown-item>Import</b-dropdown-item>
    <b-dropdown-divider></b-dropdown-divider>
    <b-dropdown-header>Global Settings</b-dropdown-header>
    <b-dropdown-item :to="{name: 'GlobalSettings-Users'}">Users</b-dropdown-item>
    <b-dropdown-item>Items</b-dropdown-item>
  </b-nav-item-dropdown>
</template>
<script>
  export default {
    name: 'settings-nav'
  };
</script>
