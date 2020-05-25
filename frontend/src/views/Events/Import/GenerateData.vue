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
      csv_type: 'Attendees',
      files: [],
      csv_types: [
        'Attendees',
        'Departments',
      ],
    };
  },
  methods: {
    generateMock() {
      const self = this;
      this.post('/api/importer/mock', {
        attendees: parseInt(self.attendees, 10),
        departments: parseInt(self.departments, 10),
        staffers: parseInt(self.staffers, 10),
        event: self.$store.state.events.event.id,
      }).then(() => {
        self.$store.commit('open_snackbar', 'Mock data generated successfully.');
      }).catch(() => {
        self.$store.commit('open_snackbar', 'Network error while generating mock data.');
      });
    },
  },
};
</script>

<style scoped>

</style>
