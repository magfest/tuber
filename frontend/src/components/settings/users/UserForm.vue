<template>
  <form @submit.prevent class="wideform">
    <div class="field">
      <label for="un">Username</label><br>
      <InputText id="un" autocomplete="off" v-model="data.username" /><br>
    </div>

    <div class="field">
      <label for="em">Email</label><br>
      <InputText id="em" autocomplete="off" v-model="data.email" /><br>
    </div>

    <div class="field">
      <label for="pa">Password</label><br>
      <InputText id="pa" type="password" autocomplete="new-password" v-model="data.newPassword" /><br>
      <small>Enter new password to reset it</small>
    </div>

    <div class="field-checkbox">
      <Checkbox id="active" v-model="data.active" :binary="true" />
      <label for="active">Active</label>
    </div>

  </form>
</template>

<script>
export default {
  name: 'UserForm',
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
