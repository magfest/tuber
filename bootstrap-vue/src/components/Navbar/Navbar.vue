<template>
  <b-navbar toggleable="lg" type="dark" variant="dark">
    <b-navbar-brand :to="{name: 'Home'}">Tuber</b-navbar-brand>

    <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>

    <b-collapse id="nav-collapse" is-nav>
      <b-navbar-nav class="ml-auto">
        <EventSelector/>
      </b-navbar-nav>
    </b-collapse>
  </b-navbar>
</template>

<script>

  import EventSelector from './EventSelector';
  export default {
    name: 'Navbar',
    components: { EventSelector },
  };
</script>

<style scoped>

</style>
