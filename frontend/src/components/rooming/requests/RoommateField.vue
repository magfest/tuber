<template>
<div>
  <AutoComplete v-model="roommates" field="public_name" forceSelection :multiple="true" :suggestions="suggestedNames" @complete="completeNames($event)" @item-select="updated" @item-unselect="updated" />
</div>
</template>

<style>
</style>

<script lang="ts">
import { Options, Vue } from 'vue-class-component'
import { PropType } from 'vue'

import AutoComplete from 'primevue/autocomplete'
import { Badge } from '../../../lib/interfaces'

@Options({
  name: 'roommate-field',
  props: {
    modelValue: Object,
    badges: Object as PropType<Badge[]>
  },
  components: {
    AutoComplete: AutoComplete
  },
  data () {
    return {
      suggestedNames: [],
      roommates: []
    }
  },
  computed: {
    badgeLookup () {
      const lookup: {[key:number]: Badge} = {}
      this.badges.forEach((badge: Badge) => {
        lookup[badge.id] = badge
      })
      return lookup
    }
  },
  watch: {
    badgeLookup () {
      this.roommates = []
      this.modelValue.forEach((val: number) => {
        this.roommates.push(this.badgeLookup[val])
      })
    },
    modelValue () {
      this.roommates = []
      this.modelValue.forEach((val: number) => {
        this.roommates.push(this.badgeLookup[val])
      })
    }
  },
  mounted () {
    this.roommates = []
    this.modelValue.forEach((val: number) => {
      this.roommates.push(this.badgeLookup[val])
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
