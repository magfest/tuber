<template>
    <div :class="containerClass" @click="onWrapperClick">
        <AppTopBar @menu-toggle="onMenuToggle" />
        <div class="layout-sidebar" @click="onSidebarClick">
            <AppMenu :model="menu" @menuitem-click="onMenuItemClick" />
        </div>

        <div class="layout-main-container">
            <div class="layout-main">
              <div class="card">
                <login v-if="(loggedIn === false) & (initialSetup === false) & !($route.name === 'uberlogin') & !($route.name === 'uberdepartmentlogin')" />
                <router-view v-else-if="event" />
              </div>
            </div>
            <AppFooter />
        </div>

        <transition name="layout-mask">
            <div class="layout-mask p-component-overlay" v-if="mobileMenuActive"></div>
        </transition>
    </div>
</template>

<script lang="ts">
import { mapGetters } from 'vuex'
import { Options, Vue } from 'vue-class-component'
import { checkPermission } from './lib/permissions'

import AppTopBar from './AppTopbar.vue'
import AppMenu from './AppMenu.vue'
import AppFooter from './AppFooter.vue'
import InitialSetup from './views/setup/InitialSetup.vue'
import Login from './views/Login.vue'
import { AppActionTypes } from './store/modules/app/actions'

type ColorMode = 'dark' | 'light'
type LayoutMode = 'static' | 'overlay'

@Options({
  data () {
    return {
      layoutMode: 'static',
      layoutColorMode: 'light',
      staticMenuInactive: true,
      overlayMenuActive: false,
      mobileMenuActive: false,
      menu: [
        {
          label: 'My Home',
          items: [{
            label: 'Dashboard', icon: 'pi pi-fw pi-home', to: '/'
          },
          {
            label: 'Room Request', icon: 'pi pi-fw pi-home', to: '/rooming/request', permission: 'rooming.*.request'
          },
          {
            label: 'Shifts', icon: 'pi pi-fw pi-home', to: '/', visible: false
          },
          {
            label: 'Checklist', icon: 'pi pi-fw pi-home', to: '/', visible: false
          }]
        },
        {
          label: 'Department Home',
          visible: false,
          items: [{
            label: 'Dashboard', icon: 'pi pi-fw pi-home', to: '/'
          },
          {
            label: 'Shifts', icon: 'pi pi-fw pi-home', to: '/'
          },
          {
            label: 'Checklist', icon: 'pi pi-fw pi-home', to: '/'
          },
          {
            label: 'Members', icon: 'pi pi-fw pi-home', to: '/'
          }]
        },
        {
          label: 'Personnel',
          permission: 'personnel.*.read',
          items: [{
            label: 'Rooming',
            permission: 'rooming.*.write',
            items: [
              {
                label: 'Requests', icon: 'pi pi-fw pi-home', to: '/rooming/requests'
              },
              {
                label: 'Approvals', icon: 'pi pi-fw pi-home', to: '/rooming/approvals', visible: false
              },
              {
                label: 'Assignments', icon: 'pi pi-fw pi-home', to: '/rooming/assignments'
              },
              {
                label: 'Rooms', icon: 'pi pi-fw pi-home', to: '/rooming/rooms'
              },
              {
                label: 'Blocks', icon: 'pi pi-fw pi-home', to: '/rooming/blocks'
              },
              {
                label: 'Settings', icon: 'pi pi-fw pi-home', to: '/rooming/settings'
              }]
          },
          {
            label: 'Perks',
            visible: false,
            items: [{
              label: 'Merch', icon: 'pi pi-fw pi-home', to: '/', visible: false
            },
            {
              label: 'Food', icon: 'pi pi-fw pi-home', to: '/', visible: false
            }]
          },
          {
            label: 'Shifts', icon: 'pi pi-fw pi-home', to: '/', visible: false
          }]
        },
        {
          label: 'Event',
          permission: 'event.*.write',
          items: [{
            label: 'Badges', icon: 'pi pi-fw pi-home', to: '/badges'
          },
          {
            label: 'Schedule', icon: 'pi pi-fw pi-home', to: '/', visible: false
          },
          {
            label: 'Emails', icon: 'pi pi-fw pi-home', to: '/', visible: false
          },
          {
            label: 'Settings', icon: 'pi pi-fw pi-home', to: '/', visible: false
          }]
        },
        {
          label: 'Server',
          permission: 'server.*.write',
          items: [{
            label: 'Import/Export', icon: 'pi pi-fw pi-home', to: '/', visible: false
          },
          {
            label: 'Users', icon: 'pi pi-fw pi-home', to: '/settings/users'
          },
          {
            label: 'Settings', icon: 'pi pi-fw pi-home', to: '/', visible: false
          }]
        }
      ]
    }
  },
  watch: {
    $route () {
      this.menuActive = false
      this.$toast.removeAllGroups()
    },
    permissions () {
      this.refreshMenu(this.menu)
    },
    event () {
      this.refreshMenu(this.menu)
    },
    departmentPermissions () {
      this.refreshMenu(this.menu)
    }
  },
  methods: {
    refreshMenu (menu: [{visible: boolean, permission?: string, items?: []}]) {
      menu.forEach((menuitem) => {
        if (Object.prototype.hasOwnProperty.call(menuitem, 'permission') && menuitem.permission) {
          menuitem.visible = checkPermission(menuitem.permission)
        }
        if (Object.prototype.hasOwnProperty.call(menuitem, 'items')) {
          this.refreshMenu(menuitem.items)
        }
      })
    },
    onWrapperClick () {
      if (!this.menuClick) {
        this.overlayMenuActive = false
        this.mobileMenuActive = false
      }

      this.menuClick = false
    },
    onMenuToggle () {
      this.menuClick = true

      if (this.isDesktop()) {
        if (this.layoutMode === 'overlay') {
          if (this.mobileMenuActive === true) {
            this.overlayMenuActive = true
          }

          this.overlayMenuActive = !this.overlayMenuActive
          this.mobileMenuActive = false
        } else if (this.layoutMode === 'static') {
          this.staticMenuInactive = !this.staticMenuInactive
        }
      } else {
        this.mobileMenuActive = !this.mobileMenuActive
      }

      if (event) {
        event.preventDefault()
      }
    },
    onSidebarClick () {
      this.menuClick = true
    },
    onMenuItemClick (event: any) {
      if (event.item && !event.item.items) {
        this.overlayMenuActive = false
        this.mobileMenuActive = false
      }
    },
    onLayoutChange (layoutMode: LayoutMode) {
      this.layoutMode = layoutMode
    },
    onLayoutColorChange (layoutColorMode: ColorMode) {
      this.layoutColorMode = layoutColorMode
    },
    addClass (element: HTMLElement, className: string) {
      if (element.classList) { element.classList.add(className) } else { element.className += ' ' + className }
    },
    removeClass (element: HTMLElement, className: string) {
      if (element.classList) { element.classList.remove(className) } else { element.className = element.className.replace(new RegExp('(^|\\b)' + className.split(' ').join('|') + '(\\b|$)', 'gi'), ' ') }
    },
    isDesktop () {
      return window.innerWidth >= 992
    },
    isSidebarVisible () {
      if (this.isDesktop()) {
        if (this.layoutMode === 'static') { return !this.staticMenuInactive } else if (this.layoutMode === 'overlay') { return this.overlayMenuActive }
      }

      return true
    }
  },
  computed: {
    ...mapGetters([
      'user',
      'event',
      'loggedIn',
      'initialSetup',
      'permissions',
      'departmentPermissions'
    ]),
    containerClass () {
      return ['layout-wrapper', {
        'layout-overlay': this.layoutMode === 'overlay',
        'layout-static': this.layoutMode === 'static',
        'layout-static-sidebar-inactive': this.staticMenuInactive && this.layoutMode === 'static',
        'layout-overlay-sidebar-active': this.overlayMenuActive && this.layoutMode === 'overlay',
        'layout-mobile-sidebar-active': this.mobileMenuActive,
        'p-input-filled': this.$primevue.config.inputStyle === 'filled',
        'p-ripple-disabled': this.$primevue.config.ripple === false,
        'layout-theme-light': this.$appState.theme.startsWith('saga')
      }]
    },
    logo () {
      return (this.layoutColorMode === 'dark') ? 'images/logo-white.svg' : 'images/logo.svg'
    }
  },
  beforeUpdate () {
    if (this.mobileMenuActive) { this.addClass(document.body, 'body-overflow-hidden') } else { this.removeClass(document.body, 'body-overflow-hidden') }
  },
  mounted () {
    this.$store.dispatch(AppActionTypes.GET_INITIAL_SETUP).then(() => {
      if (this.initialSetup) {
        this.$router.push('/initialsetup/welcome')
      }
    })
    this.$store.dispatch(AppActionTypes.GET_LOGGED_IN)
  },
  components: {
    AppTopBar: AppTopBar,
    AppMenu: AppMenu,
    AppFooter: AppFooter,
    InitialSetup: InitialSetup,
    Login: Login
  }
})
export default class App extends Vue {}
</script>

<style lang="scss">
@import './App.scss';
</style>
