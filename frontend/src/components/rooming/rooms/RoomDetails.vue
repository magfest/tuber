<template>
    <form @submit.prevent>
        <div class="field">
            <label for="name">Name</label><br>
            <InputText id="name" v-model="data.name" /><br>
          </div><br>

          <div class="field">
            <label for="messages">Messages</label><br>
            <Textarea id="messages" v-model="data.messages" /><br>
          </div><br>

          <div class="field">
            <label for="notes">Notes</label><br>
            <Textarea id="notes" v-model="data.notes" /><br>
          </div><br>
    </form>
</template>

<script>

export default {
  name: 'RoomDetails',
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
