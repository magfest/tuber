<template>
    <form @submit.prevent class="wideform">
        <div class="field">
            <label for="name">Name</label><br />
            <InputText v-model="data.name" id="name" type="text" placeholder="New Event" />
        </div>

        <div class="field">
            <label for="description">Description</label><br />
            <InputText v-model="data.description" id="description" type="text" placeholder="Describe this event" />
        </div>

        <div class="field">
            <label for="description">Uber Server URL</label><br />
            <InputText v-model="data.uber_url" id="url" type="text" placeholder="https://event2035.reg.magfest.org/jsonrpc/" />
        </div>

        <div class="field">
            <label for="description">Uber API Key</label><br />
            <InputText v-model="data.uber_apikey" id="apikey" type="text" placeholder="API key with Read/Write permissions" />
        </div>

        <div class="field">
            <label for="description">Uber Event Slug</label><br />
            <InputText v-model="data.uber_slug" id="slug" type="text" placeholder="event2035" />
        </div>

        <div class="field-checkbox">
            <Checkbox id="readonly" v-model="data.readonly" :binary="true" />
            <label for="readonly">Read-Only</label>
        </div>

        <div class="field">
          <label for="timezone">Time Zone</label><br>
          <Dropdown id="timezone" v-model="data.timezone" :options="timezones" placeholder="Select a time zone" />
        </div>
    </form>
</template>

<style scoped>

</style>

<script>
export default {
  name: 'EventForm',
  components: {
  },
  props: [
    'modelValue'
  ],
  data () {
    return {
      data: this.modelValue,
      timezones: Intl.supportedValuesOf('timeZone')
    }
  }
}
</script>
