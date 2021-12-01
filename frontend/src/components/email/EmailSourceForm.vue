<template>
    <form @submit.prevent class="wideform">
        <div class="field">
            <label for="name">Name</label><br />
            <InputText v-model="data.name" id="name" type="text" placeholder="Email Source" />
        </div>

        <div class="field">
            <label for="description">Description</label><br />
            <InputText v-model="data.description" id="description" type="text" placeholder="Description" />
        </div>

        <div class="field-checkbox">
            <Checkbox id="active" v-model="data.active" :binary="true" />
            <label for="active">Active</label>
        </div>

        <div class="field">
            <label for="address">address</label><br />
            <InputText v-model="data.address" id="address" type="text" placeholder="Email Address" />
        </div>

        <div class="field">
            <label for="region">Region</label><br />
            <InputText v-model="data.region" id="region" type="text" placeholder="AWS Region" />
        </div>

        <div class="field">
            <label for="ses_access_key">SES Access Key</label><br />
            <InputText v-model="data.ses_access_key" id="ses_access_key" type="text" placeholder="SES Access Key" />
        </div>

        <div class="field">
            <label for="ses_secret_key">SES Secret Key</label>
            <InputText v-model="data.ses_secret_key" id="ses_secret_key" type="text" placeholder="SES Secret Key" />
        </div>
    </form>
</template>

<style scoped>

</style>

<script>
export default {
  name: 'EmailSourceForm',
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
