<template>
<div class="navbar-font">
  <b-navbar toggleable="lg" type="dark" variant="dark">
    <b-navbar-brand :to="{name: 'Home'}">Tuber</b-navbar-brand>
    <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>
    <b-collapse id="nav-collapse" is-nav>
      <b-navbar-nav>
        <hotel-nav/>
        <settings-nav/>
        <shifts-nav/>
        <b-nav-item to="#">Logout</b-nav-item>
      </b-navbar-nav>
      <b-navbar-nav class="ml-auto">
        <EventSelector/>
      </b-navbar-nav>
    </b-collapse>
  </b-navbar>
</div>
</template>

<script>

  import EventSelector from './EventSelector';
  import HotelNav from './HotelNav';
  import SettingsNav from './SettingsNav';
  import ShiftsNav from './ShiftsNav';

  export default {
    name: 'Navbar',
    components: { ShiftsNav, SettingsNav, HotelNav, EventSelector },
  };
</script>

<style scoped lang="scss">
.navbar-font {
  font-size: 24px !important;
  font-family: 'Montserrat', sans-serif;
  .navbar-brand {
    font-size: 40px;
  }
}
</style>

