<template>
  <div>
    <main-navbar
      :drawer="drawer"
      @toggleDrawer="drawer = !drawer"
      :filtered_menus="filtered_menus"
    />

    <drawer
      :drawer="drawer"
      :filtered_menus="filtered_menus"
    />
  </div>
</template>

<script>
import MainNavbar from './mainNavbar.vue';
import Drawer from './drawer.vue';

export default {
  name: 'navbar.vue',
  components: { Drawer, MainNavbar },
  data() {
    return {
      drawer: null,
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
            {
              name: 'Events',
              alt: 'Add or Edit Events',
              icon: 'event',
              path: '/events',
              permissions: [
                'events.read',
              ],
            },
          ],
        },
      ],
    };
  },
  computed: {
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
  },
};
</script>

<style scoped>

</style>
