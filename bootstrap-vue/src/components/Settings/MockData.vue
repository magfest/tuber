<template>
  <div>
    <b-form @submit="generate">
      <b-form-group
        label="Attendees"
        label-for="attendee-input"
        description="How many attendees to generate"
      >
        <b-form-input
          id="attendee-input"
          v-model="attendees"
          type="number"
          required
        />
      </b-form-group>
      <b-form-group
        label="Staffers"
        label-for="staffers-input"
        description="How many staffers to generate"
      >
        <b-form-input
          id="staffers-input"
          v-model="staffers"
          type="number"
          required
        />
      </b-form-group>
      <b-form-group
        label="Departments"
        label-for="department-input"
        description="How many departments to generate"
      >
        <b-form-input
          id="department-input"
          v-model="departments"
          type="number"
          required
        ></b-form-input>
      </b-form-group>
      <div class="d-flex">
        <b-btn
          type="submit"
          variant="success"
          class="ml-auto"
        >Generate</b-btn>
      </div>
    </b-form>
  </div>
</template>

<script>
  import axios from 'axios';
  import {mapState} from 'vuex';

  export default {
    name: 'MockData',
    data(){
      return {
        attendees: 20000,
        departments: 50,
        staffers: 2000,
        csv_type: 'Attendees',
        files: [],
        csv_types: [
          'Attendees',
          'Departments'
        ]
      }
    },

    computed: {
      ...mapState('events', ['event'])
    },

    methods: {
      generate(evt){
        evt.preventDefault();
        axios.post('importer/mock', {
          attendees: parseInt(this.attendees),
          departments: parseInt(this.departments),
          staffers: parseInt(this.staffers),
          event: this.event.id
        })
          .then(() => {
            this.$notify({
              group: 'main',
              title: 'Success',
              text: 'Generate complete'
            })
          })
          .catch(() => {
            this.$notify({
              group: 'main',
              title: 'Failure',
              text: 'Something went wrong generating data'
            })
          })
      }
    }
  };
</script>

<style scoped>

</style>
