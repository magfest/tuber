<template>
  <div class="container">
    <div class="d-flex justify-center">
      <h2>Jobs</h2>
    </div>
    <div class="d-flex justify-center" v-if="jobs.length === 0">
      No currently visible jobs
    </div>

    <NewJob/>
  </div>
</template>

<script>
  import { mapAsyncDump } from '../../mixins/rest';
  import NewJob from '../../components/jobs/NewJob';

  export default {
    name: 'ListJobs',
    components: { NewJob },
    asyncComputed: {
      ...mapAsyncDump([
        'jobs'
      ])
    }
  };
</script>

<style scoped>

</style>
