<template>
  <AutoComplete v-model="internalvalue" field="search_name" forceSelection :multiple="true" :suggestions="suggestedNames" @complete="completeNames($event)" />
</template>

<style>
</style>

<script lang="ts">
import AutoComplete from 'primevue/autocomplete'
import { get } from '../../lib/rest'
import { Badge } from '../../lib/interfaces'
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'roommate-field',
  props: ['value'],
  components: {
    AutoComplete: AutoComplete
  },
  data: (): {suggestedNames: Badge[], badges: Badge[]} => ({
    suggestedNames: [],
    badges: []
  }),
  computed: {
    internalvalue: {
      get (): string[] {
        return this.value
      },
      set (val: string[]) {
        this.$emit('input', val)
      }
    }
  },
  asyncComputed: {
  },
  mounted () {
    get('/api/event/1/badge').then((res: Badge[]) => {
      this.badges = res
    })
  },
  methods: {
    completeNames (event: {query: string}) {
      this.suggestedNames = []
      this.badges.forEach((badge: Badge) => {
        if (badge.search_name) {
          if (badge.search_name.startsWith(event.query)) {
            this.suggestedNames.push(badge)
          }
        }
      })
    }
  }
})
</script>
