<template>
    <form @submit.prevent class="wideform">
        <div class="field">
            <label for="name">Name</label><br />
            <InputText v-model="data.name" id="name" type="text" placeholder="New Event" />
        </div>

        <div class="field">
            <label for="description">Description</label><br />
            <InputText v-model="data.description" id="description" type="text" placeholder="Describe this email" />
        </div>

        <div class="field-checkbox">
            <Checkbox id="readonly" v-model="eventModel.readonly" :binary="true" />
            <label for="readonly">Read-Only</label>
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
      data: this.modelValue
    }
  }
}
</script>
