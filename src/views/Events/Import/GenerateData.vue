<template>
  <v-tab-item>
    <v-form>
      <p>This tool generates testing data.</p>
      <p>How much test data should be generated?</p>
      <v-text-field label="Number of Attendees" v-model="attendees" outlined/>
      <v-text-field label="Number of Staffers" v-model="staffers" outlined/>
      <v-text-field label="Number of Departments" v-model="departments" outlined/>
      <v-card-actions>
        <v-spacer/>
        <v-btn outlined type="submit" @click.prevent="generateMock">Generate</v-btn>
      </v-card-actions>
    </v-form>
  </v-tab-item>
</template>

<script>
export default {
  name: 'GenerateData',
  data() {
    return {
      attendees: 50000,
      departments: 50,
      staffers: 2000,
    };
  },
  methods: {
    generateMock() {

    },
  },
};
</script>

<style scoped>

</style>
