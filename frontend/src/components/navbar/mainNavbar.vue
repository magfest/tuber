<template>
  <v-app-bar app clipped-left>
    <v-app-bar-nav-icon  @click.stop="$emit('toggleDrawer')" class="hidden-lg-and-up"></v-app-bar-nav-icon>
    <v-toolbar-title>
      <span @click="$router.push({name: 'home'})" style="cursor: pointer" class="pr-md-10">Tuber</span>
    </v-toolbar-title>
    <div v-for="navmenu in filtered_menus" :key="navmenu.name" class="px-md-2 hidden-md-and-down">
      <v-menu offset-y>
        <template v-slot:activator="{ on }">
          <v-btn v-on="on" :alt="navmenu.alt">
            <v-icon left>{{ navmenu.icon }}</v-icon>{{ navmenu.name }}
          </v-btn>
        </template>
        <v-list>
          <v-list-item v-for="(item, index) in navmenu.items" :key="index" @click="$router.push({path: item.path})" :alt="item.alt">
            <v-list-item-title><v-icon left>{{ item.icon }}</v-icon>{{ item.name }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </div>
    <div class="px-md-2 hidden-md-and-down">
      <v-btn alt="Logout" @click="$router.push({name: 'logout'})" v-if="logged_in">
        <v-icon left>exit_to_app</v-icon>Logout
      </v-btn>
    </div>
    <v-spacer></v-spacer>
    <div>
      <v-select class="event-select" :items="events" item-text="name" item-value="id" v-model="event" label="Event" outlined></v-select>
    </div>
  </v-app-bar>
</template>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'mainNavbar',
  props: [
    'drawer',
    'filtered_menus',
  ],
  computed: {
    ...mapGetters([
      'logged_in',
      'events',
    ]),
  },
};
</script>

<style scoped>
  .event-select {
    padding-top: 30px !important;
  }
</style>
