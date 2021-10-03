<template>
    <div :class="containerClass" @click="onWrapperClick">
        <AppTopBar @menu-toggle="onMenuToggle" />
        <div class="layout-sidebar" @click="onSidebarClick">
            <AppMenu :model="menu" @menuitem-click="onMenuItemClick" />
        </div>

        <div class="layout-main-container">
            <div class="layout-main">
                <router-view />
            </div>
            <AppFooter />
        </div>

        <transition name="layout-mask">
            <div class="layout-mask p-component-overlay" v-if="mobileMenuActive"></div>
        </transition>
    </div>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'

import AppTopBar from './AppTopbar.vue'
import AppMenu from './AppMenu.vue'
import AppFooter from './AppFooter.vue'

type ColorMode = 'dark' | 'light'
type LayoutMode = 'static' | 'overlay'

@Options({
  data () {
    return {
      layoutMode: 'static',
      layoutColorMode: 'light',
      staticMenuInactive: false,
      overlayMenuActive: false,
      mobileMenuActive: false,
      menu: [
        {
          label: 'My Home',
          items: [{
            label: 'Dashboard', icon: 'pi pi-fw pi-home', to: '/'
          },
          {
            label: 'Shifts', icon: 'pi pi-fw pi-home', to: '/shifts'
          },
          {
            label: 'Checklist', icon: 'pi pi-fw pi-home', to: '/checklist'
          }]
        },
        {
          label: 'Department Home',
          items: [{
            label: 'Dashboard', icon: 'pi pi-fw pi-home', to: '/department'
          },
          {
            label: 'Shifts', icon: 'pi pi-fw pi-home', to: '/department/shifts'
          },
          {
            label: 'Checklist', icon: 'pi pi-fw pi-home', to: '/department/checklist'
          },
          {
            label: 'Members', icon: 'pi pi-fw pi-home', to: '/department/members'
          }]
        },
        {
          label: 'Personnel',
          items: [{
            label: 'Rooming',
            items: [{
              label: 'Eligibility', icon: 'pi pi-fw pi-home', to: '/rooming/eligibility'
            },
            {
              label: 'Requests', icon: 'pi pi-fw pi-home', to: '/rooming/requests'
            },
            {
              label: 'Approvals', icon: 'pi pi-fw pi-home', to: '/rooming/approvals'
            },
            {
              label: 'Assignments', icon: 'pi pi-fw pi-home', to: '/rooming/assignments'
            },
            {
              label: 'Settings', icon: 'pi pi-fw pi-home', to: '/rooming/settings'
            }]
          },
          {
            label: 'Perks',
            items: [{
              label: 'Merch', icon: 'pi pi-fw pi-home', to: '/personnel/perks/merch'
            },
            {
              label: 'Food', icon: 'pi pi-fw pi-home', to: '/personnel/perks/food'
            }]
          },
          {
            label: 'Shifts', icon: 'pi pi-fw pi-home', to: '/personnel/shifts'
          }]
        },
        {
          label: 'Event',
          items: [{
            label: 'Badges', icon: 'pi pi-fw pi-home', to: '/event/badges'
          },
          {
            label: 'Schedule', icon: 'pi pi-fw pi-home', to: '/event/schedule'
          },
          {
            label: 'Emails', icon: 'pi pi-fw pi-home', to: '/event/emails'
          },
          {
            label: 'Settings', icon: 'pi pi-fw pi-home', to: '/event/settings'
          }]
        },
        {
          label: 'Server',
          items: [{
            label: 'Import/Export', icon: 'pi pi-fw pi-home', to: '/server/import-export'
          },
          {
            label: 'Users', icon: 'pi pi-fw pi-home', to: '/server/users'
          },
          {
            label: 'Settings', icon: 'pi pi-fw pi-home', to: '/server/settings'
          }]
        }
      ]
    }
  },
  watch: {
    $route () {
      this.menuActive = false
      this.$toast.removeAllGroups()
    }
  },
  methods: {
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
  components: {
    AppTopBar: AppTopBar,
    AppMenu: AppMenu,
    AppFooter: AppFooter
  }
})
export default class App extends Vue {}
</script>

<style lang="scss">
@import './App.scss';
</style>
