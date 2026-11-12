<template>
  <Tag v-if="preference" :severity="preference.ignored ? 'warning' : 'info'" :value="label" :title="title"
       class="single-gender-tag" />
</template>

<style scoped>
.single-gender-tag {
  font-size: 0.7rem;
  padding: 0.05rem 0.4rem;
  margin-left: 0.3rem;
  vertical-align: middle;
}
</style>

<script>
// Someone in the room asked for a single-gender room. Answers the gender map
// sends to null aren't used for matching, so those are shown for a human to
// handle instead.
export default {
  name: 'SingleGenderTag',
  props: {
    preference: {
      type: Object,
      default: null
    }
  },
  computed: {
    label () {
      if (this.preference.ignored) {
        return 'Single gender: "' + this.preference.answer + '"'
      }
      return (this.preference.group || 'gender blank') + ' only'
    },
    title () {
      if (this.preference.ignored) {
        return 'Asked for a single-gender room, but their answer isn\'t used for matching. Check with them directly.'
      }
      return 'Asked for a single-gender room (answered "' + this.preference.answer + '")'
    }
  }
}
</script>
