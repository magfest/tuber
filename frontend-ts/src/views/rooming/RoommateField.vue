<template>
<div>
  <AutoComplete v-model="roommates" field="printed_name" forceSelection :multiple="true" :suggestions="suggestedNames" @complete="completeNames($event)" @item-select="updated" @item-unselect="updated" />
</div>
</template>

<style>
</style>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'

import AutoComplete from 'primevue/autocomplete'
import { get } from '../../lib/rest'
import { Badge } from '../../lib/interfaces'

@Options({
  name: 'roommate-field',
  props: ['modelValue'],
  components: {
    AutoComplete: AutoComplete
  },
  data () {
    return {
      suggestedNames: [],
      badges: [],
      badgeLookup: {},
      roommates: []
    }
  },
  mounted () {
    get('/api/event/1/badge').then((res: Badge[]) => {
      this.badges = res
      this.badges.forEach((badge: Badge) => {
        this.badgeLookup[badge.id] = badge
      })
      this.modelValue.forEach((val: number) => [
        this.roommates.push(this.badgeLookup[val])
      ])
    })
  },
  methods: {
    updated () {
      const val: number[] = []
      this.roommates.forEach((roommate: Badge) => {
        val.push(roommate.id)
      })
      this.$emit('update:modelValue', val)
    },
    completeNames (event: {query: string}) {
      this.suggestedNames = []
      this.badges.forEach((badge: Badge) => {
        if (badge.search_name) {
          if (badge.search_name.toLowerCase().includes(event.query.toLowerCase())) {
            this.suggestedNames.push(badge)
          }
        }
      })
    }
  }
})
export default class RoommateField extends Vue {}
</script>
