<template>
  <div>
    <Toast />
    <div class="card">
        <Steps :model="items" />
        <router-view v-slot="{Component}" @nextPage="nextPage()" @complete="complete">
            <keep-alive>
                <component :is="Component" />
            </keep-alive>
        </router-view>
    </div>
  </div>
</template>

<style>
</style>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'

@Options({
  name: 'InitialSetup',
  components: {
  },
  data: () => ({
    items: [{
      label: 'Welcome',
      to: '/initialsetup/welcome'
    },
    {
      label: 'Admin User',
      to: '/initialsetup/user'
    },
    {
      label: 'Create Event',
      to: '/initialsetup/event'
    }],
    index: 0
  }),
  methods: {
    nextPage () {
      if (this.index + 1 === this.items.length) {
        this.$router.push('/')
      } else {
        this.$router.push(this.items[this.index + 1].to)
        this.index++
      }
    },
    complete () {
      this.$toast.add({ severity: 'success', summary: 'Order submitted', detail: 'Success!' })
    }
  }
})
export default class InitialSetup extends Vue {}
</script>
