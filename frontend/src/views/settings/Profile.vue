<template>
    <div class="card">
        <Toast />
        <h3>{{ user.username }}'s Profile</h3>
        <form>
            <div class="field">
                <label for="default_event">Default Event</label><br />
                <Dropdown id="default_event" v-model="user.default_event" :options="events" optionLabel="name"
                    optionValue="id" />
            </div>
        </form>
        <Button @click="save" label="Save"></Button>
    </div>
</template>

<style>

</style>

<script>
import { get, patch } from '../../lib/rest'

export default {
  name: 'Profile',
  data: () => ({
    user: {},
    events: []
  }),
  async mounted () {
    this.load()
  },
  methods: {
    async load () {
      this.user = await get('/api/user/me')
      this.events = await get('/api/event')
    },
    async save () {
      try {
        await patch('/api/user/me', this.user)
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 1000 })
        this.load()
      } catch {
        this.$toast.add({ severity: 'error', summary: 'Save Failed', detail: 'Please contact your server administrator for assistance.', life: 3000 })
      }
    }
  }
}
</script>
