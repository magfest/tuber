<template>
    <form @submit.prevent class="wideform">
        <div class="field">
            <label for="name">Name</label><br />
            <InputText v-model="data.name" id="name" type="text" placeholder="New Email" />
        </div>

        <div class="field-checkbox">
            <Checkbox id="active" v-model="data.active" :binary="true" />
            <label for="active">Active</label>
        </div>

        <div class="field-checkbox">
            <Checkbox id="send_once" v-model="data.send_once" :binary="true" />
            <label for="send_once">Send Once</label>
        </div>

        <div class="field">
            <label for="description">Description</label><br />
            <InputText v-model="data.description" id="description" type="text" placeholder="Describe this email" />
        </div>

        <div class="field">
            <label for="source">Source</label><br />
            <Dropdown id="source" v-model="data.source" :options="sources" optionLabel="name" optionValue="id" />
        </div>

        <div class="field">
            <label for="subject">Subject</label><br />
            <InputText v-model="data.subject" id="subject" type="text" placeholder="Please Read" />
        </div>

        <Textarea v-model="data.code" /><br />
        <Textarea v-model="data.body" />
    </form>
</template>

<style scoped>

</style>

<script>
import { mapGetters } from 'vuex'
import { get } from '@/lib/rest'

export default {
  name: 'EmailForm',
  components: {
  },
  props: [
    'modelValue'
  ],
  data () {
    return {
      data: this.modelValue,
      sources: []
    }
  },
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
    async load () {
      this.sources = await get('/api/event/' + this.event.id + '/email_source')
    }
  },
  watch: {
    event () {
      this.load()
    }
  }
}
</script>
