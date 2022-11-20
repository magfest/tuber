<template>
  <div>
    <div class="from">
      <span class="label">From:</span> {{ data.from_address }}
    </div>
    <div class="to">
      <span class="label">To:</span> {{ data.to_address }}
    </div>
    <div>
      <span class="label">Timestamp:</span> {{ data.timestamp }}
    </div><br />
    <div>
      <span class="label">Subject:</span> {{ data.subject }}
    </div>
    <Textarea v-model="data.body" style="width: 100%; min-height: 200px" />
  </div>
</template>

<style scoped>
.from {
  text-align: left;
  float: left;
}

.to {
  text-align: right;
}

.label {
  font-weight: bold;
}

TextArea {
  width: 100%;
  min-height: 200px;
  margin-top: 15px;
}
</style>

<script>
export default {
  name: 'EmailReceiptForm',
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
