<template>
  <v-tab-item>
    <div>Some text</div>
    <v-form>
      <p>Import data from a CSV file</p>
      <v-select
        label="CSV Type"
        outlined
        v-model="csv_type"
        :items="csv_types"/>
      <v-file-input
        label="CSV Upload"
        v-model="files"
        accept=".csv"
        show-size
        outlined/>
      <v-card-actions>
        <v-spacer/>
        <v-btn
          outlined
          type="submit"
          @click.prevent="importCSV"
        >
          Import
        </v-btn>
      </v-card-actions>
    </v-form>
  </v-tab-item>
</template>

<script>
export default {
  name: 'ImportFromCSV',
  data() {
    return {
      csv_type: '',
      csv_types: [
        'Attendees',
        'Departments',
      ],
      files: [],
    };
  },

  methods: {
    importCSV() {

    },
  },
};
</script>

<style scoped>

</style>
