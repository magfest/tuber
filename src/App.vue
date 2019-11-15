<template>
  <v-app>
    <v-app-bar app clipped-left>
      <v-app-bar-nav-icon  @click.stop="drawer = !drawer" class="hidden-lg-and-up"></v-app-bar-nav-icon>
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
            icon: 'single_bed',
            permissions: [
              'hotel_request.create',
            ],
          },
          {
            name: 'Approve Requests',
            alt: 'Approve hotel requests from staffers in your department',
            path: '/hotels/approve',
            icon: 'done',
            permissions: [
              'hotel_request.approve',
            ],
          },
          {
            name: 'Assign Rooms',
            alt: 'Assign staffers to hotel rooms',
            path: '/hotels/assign',
            icon: 'low_priority',
            permissions: [
              'hotel_assignment.read',
            ],
          },
          {
            name: 'Settings',
            alt: 'Configure the hotel system',
            path: '/hotels/settings',
            icon: 'settings',
            permissions: [
              'hotel.settings',
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
            name: 'Email Settings',
            alt: 'Edit Automated Emails',
            icon: 'email',
            path: '/emails',
            permissions: [
              'emails.read',
            ],
          },
          {
            name: 'Email Source Settings',
            alt: 'Edit Email Providers',
            icon: 'dns',
            path: '/emailsources',
            permissions: [
              'emailsource.read',
            ],
          },
          {
            name: 'Import',
            alt: 'Import Data',
            icon: 'import_export',
            path: '/event/import',
            permissions: [
              'import.*',
            ],
          },
        ],
      },
      {
        name: 'Global Settings',
        alt: 'Change Settings for Tuber',
        icon: 'settings_applications',
        items: [
          {
            name: 'Users',
            alt: 'Add or Edit Users',
            icon: 'group',
            path: '/users',
            permissions: [
              'user.read',
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
    show_hotel() {
      return this.checkPermission('hotels.read');
    },
    show_event_settings() {
      return this.checkPermission('event.read', this.event.id);
    },
  },
  mounted() {
    this.$vuetify.theme.dark = false;
  },
  methods: {
  },
  watch: {
  },
};
</script>
