<template>
  <div class="d-flex justify-center mt-5">
    <v-form @submit.prevent @submit="onSubmit">
      <div>
        Enter information for your new job
      </div>
      <v-text-field
        v-model="jobName"
        label="Name"
        required
        filled
      />
      <v-textarea
        v-model="jobDesc"
        label="Description"
        required
        filled
      />
      <v-textarea
        v-model="jobDoc"
        label="Documentation"
        filled
      />
      <v-btn type="submit" text color="success">Create</v-btn>
    </v-form>
  </div>
</template>

<script>
  import {post} from '../../mixins/rest';
  import {mapGetters} from 'vuex';

  export default {
    name: 'NewJob',

    data(){
      return {
        jobName: "",
        jobDesc: '',
        jobDoc: ''
      }
    },

    computed: {
      ...mapGetters([
        'event',
      ]),
    },

    methods: {
      onSubmit(){
        post(`/api/events/${this.event.id}/jobs`, {
          name: this.jobName,
          description: this.jobDesc,
          documentation: this.jobDoc,
        }).then(response => {
          console.log('then', response)
        }).catch((e) => {
          console.log('catch', e)
        })
      }
    }
  };
</script>

<style scoped>

</style>
