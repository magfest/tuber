<template>
  <div>
    <div v-if="active">
        <h3 v-if="message">{{ status }}</h3>
        <ProgressBar :value="amount" :mode="mode"></ProgressBar>
        <pre v-if="log">{{ messages }}</pre>
    </div>
  </div>
</template>

<script lang='ts'>
import { Options, Vue } from 'vue-class-component'
import { Progress } from '../lib/rest'

@Options({
  name: 'LoadingBar',
  props: {
    log: false,
    message: false
  },
  data () {
    return {
      active: false,
      definite: false,
      status: '',
      messages: '',
      amount: 0
    }
  },
  computed: {
    mode () {
      if (this.definite) {
        return 'determinate'
      }
      return 'indeterminate'
    }
  },
  methods: {
    update (progress: Progress) {
      console.log('Progress')
      this.active = progress.active
      this.definite = progress.definite
      this.status = progress.status
      this.messages = progress.messages
      this.amount = progress.amount * 100
    }
  }
})

export default class LoadingBar extends Vue {}
</script>
