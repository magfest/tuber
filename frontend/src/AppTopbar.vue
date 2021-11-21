<template>
    <div class="layout-topbar">
        <router-link to="/" class="layout-topbar-logo">
            <img alt="Logo" src="/images/logo-dark.svg" />
            <span>Tuber</span>
        </router-link>
        <button class="p-link layout-menu-button layout-topbar-button" @click="onMenuToggle">
            <i class="pi pi-bars"></i>
        </button>

        <button class="p-link layout-topbar-menu-button layout-topbar-button"
            v-styleclass="{ selector: '@next', enterClass: 'hidden', enterActiveClass: 'scalein',
            leaveToClass: 'hidden', leaveActiveClass: 'fadeout', hideOnOutsideClick: true}">
            <i class="pi pi-ellipsis-v"></i>
        </button>
        <ul class="layout-topbar-menu hidden lg:flex origin-top">
            <li>
              <Dropdown class="mt-2" v-if="loggedIn & events.length > 0" :modelValue="activeEvent" :options="events" optionValue="id" optionLabel="name" @change="updateEvent" placeHolder="Select an Event" />
            </li>
            <li>
                <button class="p-link layout-topbar-button" @click="toggleUserMenu">
                    <i class="pi pi-user"></i>
                    <span>Profile</span>
                </button>
                <Menu ref="userMenu" :model="userMenuItems" :popup="true" />
            </li>
        </ul>
    </div>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'
import { mapGetters } from 'vuex'
import { AppActionTypes } from './store/modules/app/actions'

@Options({
  data: (): {} => ({
    userMenuItems: [
      {
        label: 'Account',
        items: [
          { label: 'Sign Out', visible: false, icon: 'pi pi-fw pi-power-off', to: '/logout' },
          { label: 'Sign In', visible: true, icon: 'pi pi-fw pi-power-on', to: '/login' }
        ]
      }
    ],
    activeEvent: null
  }),
  methods: {
    onMenuToggle (event: Event) {
      this.$emit('menu-toggle', event)
    },
    onTopbarMenuToggle (event: Event) {
      this.$emit('topbar-menu-toggle', event)
    },
    updateEvent (e: {value: {}}) {
      for (const evt of this.events) {
        if (evt.id === e.value) {
          this.$store.dispatch(AppActionTypes.SET_EVENT, evt)
        }
      }
    },
    toggleUserMenu (e: Event) {
      this.$refs.userMenu.toggle(e)
    },
    refreshTopBar () {
      if (this.loggedIn) {
        this.userMenuItems[0].items[0].visible = true
        this.userMenuItems[0].items[1].visible = false
      } else {
        this.userMenuItems[0].items[0].visible = false
        this.userMenuItems[0].items[1].visible = true
      }
    }
  },
  computed: {
    ...mapGetters([
      'loggedIn',
      'events',
      'event',
      'user',
      'badge'
    ])
  },
  watch: {
    loggedIn () {
      this.refreshTopBar()
    },
    event () {
      if (this.event) {
        this.activeEvent = this.event.id
      } else {
        this.activeEvent = null
      }
    }
  },
  mounted () {
  }
})
export default class AppTopBar extends Vue {}
</script>
