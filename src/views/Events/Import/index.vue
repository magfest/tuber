<template>
  <v-card
    max-width="1000"
    :raised="true"
    class="mx-auto mt-4"
    :loading="loading">
    <v-card-title>Import Data</v-card-title>
    <v-card-text>
      <v-tabs v-model="tab">
        <v-tab>
          Uber
        </v-tab>
        <v-tab>
          CSV
        </v-tab>
        <ImportFromCSV/>
        <v-tab>
          Mock Data
        </v-tab>
      </v-tabs>

      <v-tabs-items v-model="tab">
        <LoginFromUber/>
        <ImportFromCSV/>
        <GenerateData/>
      </v-tabs-items>
    </v-card-text>
  </v-card>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';
import LoginFromUber from './LoginFromUber.vue';
import ImportFromCSV from './ImportFromCSV.vue';
import GenerateData from './GenerateData.vue';

export default {
  name: 'DataImporter',
  components: {
    GenerateData,
    ImportFromCSV,
    LoginFromUber,
  },
  data: () => ({
    tab: null,
    loading: false,
    email: '',
    password: '',
    uber_url: '',
    attendees: 50000,
    departments: 50,
    staffers: 2000,
    csv_type: 'Attendees',
  }),
  computed: {
    ...mapGetters([
      'event',
    ]),
  },
  methods: {
    generateMock() {

    },
  },
};
</script>
