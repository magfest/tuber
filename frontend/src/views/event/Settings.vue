<template>
  <div class="card">
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <h3>Event Settings</h3>
    <form @submit.prevent class="wideform">
      <div class="field">
        <label for="name">Name</label><br />
        <InputText v-model="eventModel.name" id="name" type="text" placeholder="New Event" />
      </div>

      <div class="field">
        <label for="description">Description</label><br />
        <InputText v-model="eventModel.description" id="description" type="text" placeholder="Describe this email" />
      </div>

      <div class="field-checkbox">
        <Checkbox id="readonly" v-model="eventModel.readonly" :binary="true" />
        <label for="readonly">Read-Only</label>
      </div>

      <Button label="Save" @click="save()" autofocus />
    </form>
  </div>
</template>

<style>

</style>

<script>
import { mapGetters } from 'vuex'
import { get, patch } from '../../lib/rest'

export default {
  name: 'EventSettings',
  data: () => ({
    eventModel: {
      name: '',
      description: '',
      readonly: false
    }
  }),
  computed: {
    ...mapGetters([
      'event'
    ])
  },
  mounted () {
    if (this.event) {
      this.load()
    }
  },
  methods: {
    async save () {
      await patch('/api/event/' + this.event.id, this.eventModel)
      this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 1000 })
      this.load()
    },
    async load () {
      this.loading = true
      if (this.event) {
        this.eventModel = await get('/api/event/' + this.event.id)
        this.loading = false
      }
    }
  },
  watch: {
    event () {
      this.load()
    }
  }
}
</script>
