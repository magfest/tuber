<template>
  <v-navigation-drawer v-model="drawer" temporary absolute width = "400" id = "drawer">
    <v-toolbar-title>
      <span class="mx-auto">Tuber</span>
    </v-toolbar-title>
    <v-divider>
    </v-divider>
    <v-expansion-panels>
      <v-expansion-panel v-for="navmenu in filtered_menus" :key="navmenu.name">
        <v-expansion-panel-header>
          <div>{{ navmenu.name }}</div>
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-list>
            <v-list-item v-for="(item, index) in navmenu.items" :key="index" @click="$router.push({path: item.path})" :alt="item.alt">
              <v-list-item-title><v-icon left>{{ item.icon }}</v-icon>{{ item.name }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-expansion-panel-content>
      </v-expansion-panel>
      <v-expansion-panel alt="Logout" @click="$router.push({name: 'logout'})" v-if="logged_in">
        <v-expansion-panel-header expand-icon="">
          Logout
        </v-expansion-panel-header>
      </v-expansion-panel>
    </v-expansion-panels>
  </v-navigation-drawer>
</template>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'drawer',
  props: [
    'drawer',
    'filtered_menus',
  ],
  computed: {
    ...mapGetters([
      'logged_in',
    ]),
  },
};
</script>

<style scoped>

</style>
