<template>
    <form @submit.prevent class="wideform">
        <div class="field">
            <label for="name">Name</label>
            <InputText v-model="data.name" id="name" type="text" placeholder="New Email" />
        </div>
    </form>
</template>

<style scoped>

</style>

<script>
export default {
  name: 'EmailTriggerForm',
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
