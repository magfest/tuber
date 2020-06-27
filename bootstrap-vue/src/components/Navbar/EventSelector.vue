<template>
  <b-nav-form>
    <b-form-select :options="parsedEvents" v-model="selectedEvent" @change="() => {setEvent(selectedEvent)}"/>
  </b-nav-form>
</template>

<script>
  import { mapState, mapMutations } from 'vuex';

  export default {
    name: 'EventSelector',

    data(){
      return {
        selectedEvent: '',
      }
    },

    methods: {
      ...mapMutations('events', ['setEvent']),
    },

    computed: {
      ...mapState('events', ['events']),

      parsedEvents(){
        return this.events.map(event => {return {
          value: event.name,
          text: event.name
        }})
      }
    }
  };
</script>

<style scoped>

</style>
