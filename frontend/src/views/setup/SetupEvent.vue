<template>
  <div class="card">
    <h3>Create Your First Event</h3>
    <p>Start out by giving us some basic information about your event.</p>
    <form @submit.prevent>
      <div class="field grid">
          <label for="name" class="col-fixed" style="width:100px">Name</label>
          <div class="col">
              <InputText id="name" v-model="event.name" type="text" />
          </div>
      </div>
      <div class="field grid">
          <label for="description" class="col-fixed" style="width:100px">Description</label>
          <div class="col">
              <InputText id="description" v-model="event.description" type="text" />
          </div>
      </div>
      <div class="grid justify-content-between">
        <div></div>
        <Button type="submit" label="Finish" @click="createEvent" icon="pi pi-angle-right" iconPos="right" />
      </div>
    </form>
  </div>
</template>

<style>
</style>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'
import { post } from '../../lib/rest'
import { AppActionTypes } from '../../store/modules/app/actions'

@Options({
  name: 'SetupEvent',
  data: () => ({
    event: {
      name: '',
      description: ''
    }
  }),
  methods: {
    createEvent: async function () {
      try {
        await post('/api/event', this.event)
        await this.$store.dispatch(AppActionTypes.GET_EVENTS)
        this.$emit('nextPage')
      } catch (e) {
        console.log('Failed to create event!', e)
      } finally {
        console.log('resetting')
      }
    }
  }
})
export default class SetupUser extends Vue {}
</script>
