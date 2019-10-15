<template>
  <v-app>
    <v-app-bar app clipped-left>
      <v-app-bar-nav-icon  @click.stop="drawer = !drawer" class="hidden-lg-and-up"></v-app-bar-nav-icon>
      <v-toolbar-title>
        <span class="pr-md-10">Tuber</span>
      </v-toolbar-title>
      <div class="hidden-md-and-down">
        <v-menu class="px-md-1" offset-y v-for="navmenu in filtered_menus" :key="navmenu.name">
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
      <div class="px-md-4 hidden-md-and-down">
      <v-btn alt="Logout" @click="$router.push({name: 'logout'})" v-if="logged_in">
        Logout
      </v-btn>
      </div>
      <v-spacer></v-spacer>
      <div>
        <v-select class="event-select" :items="events" item-text="name" item-value="id" v-model="event" label="Event" outlined></v-select>
      </div>
    </v-app-bar>

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

    <v-content>
      <transition name="slide">
        <router-view/>
      </transition>
    </v-content>
    <v-snackbar v-model="snackbar_open">
      {{ snackbar_text }}
      <v-btn color="pink" text @click="$store.commit('close_snackbar')">Close</v-btn>
    </v-snackbar>
  </v-app>
</template>

<style>
.event-select {
  padding-top: 30px !important;
}
</style>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'App',
  data: () => ({
    drawer: null,
    selected_event: {},
    show_hotel: false,
    show_event_settings: false,
    menu: [
      {
        name: 'Hotels',
        alt: 'Assign Staffers to Rooms',
        icon: 'hotel',
        items: [
          {
            name: 'Room Request',
            alt: 'Request a hotel room for yourself',
            path: '/hotels/request',
            icon: 'settings',
            permissions: [
              'hotelrequest.read',
            ],
          },
          {
            name: 'Approve Requests',
            alt: 'Approve hotel requests from staffers in your department',
            path: '/hotels/approve',
            icon: 'settings',
            permissions: [
              'hotelrequest.write',
            ],
          },
          {
            name: 'Assign Rooms',
            alt: 'Assign staffers to hotel rooms',
            path: '/hotels/assign',
            icon: 'settings',
            permissions: [
              'hotelassignment.read',
            ],
          },
        ],
      },
      {
        name: 'Event Settings',
        alt: 'Change Event-Global Settings',
        icon: 'settings',
        items: [
          {
            name: 'Event Settings',
            alt: 'Change Event-Global Settings',
            icon: 'settings',
            path: '/event/settings',
            permissions: [
              'event.write',
            ],
          },
          {
            name: 'Import Staff',
            alt: 'Import staff from Uber',
            icon: 'import_export',
            path: '/import/staff',
            permissions: [
              'import.staff',
            ],
          },
        ],
      },
    ],
  }),
  computed: {
    ...mapGetters([
      'snackbar_text',
      'initial_setup',
      'user',
      'logged_in',
      'events',
    ]),
    filtered_menus() {
      const filtered = [];
      for (let i = 0; i < this.menu.length; i += 1) {
        const submenu = [];
        for (let j = 0; j < this.menu[i].items.length; j += 1) {
          let allowed = true;
          for (let k = 0; k < this.menu[i].items[j].permissions.length; k += 1) {
            if (!this.checkPermission(this.menu[i].items[j].permissions[k])) {
              allowed = false;
            }
          }
          if (allowed) {
            submenu.push(this.menu[i].items[j]);
          }
        }
        if (submenu.length > 0) {
          filtered.push({
            name: this.menu[i].name,
            alt: this.menu[i].alt,
            icon: this.menu[i].icon,
            items: submenu,
          });
        }
      }
      return filtered;
    },
    snackbar_open: {
      get() {
        return this.$store.state.snackbar.snackbar;
      },
      set(value) {
        if (!value) {
          this.$store.commit('close_snackbar');
        }
      },
    },
    event: {
      get() {
        return this.$store.state.events.event;
      },
      set(value) {
        const self = this;
        this.events.forEach((el) => {
          if (el.id === value) {
            self.$store.commit('set_event', el);
          }
        });
      },
    },
  },
  mounted() {
    this.$vuetify.theme.dark = false;
  },
  methods: {
    updateMenus() {
      this.show_hotel = this.checkPermission('hotels.read');
      this.show_event_settings = this.checkPermission('event.read', this.event.id);
    },
  },
  watch: {
    user() {
      const self = this;
      this.$store.dispatch('get_events').then(() => {
        self.updateMenus();
      });
    },
    event() {
      this.updateMenus();
    },
  },
};
</script>
