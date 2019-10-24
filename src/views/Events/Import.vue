<template>
  <div>
    <div>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Import Data</v-card-title>
        <v-card-text>
          <v-tabs>
            <v-tab>
              Uber
            </v-tab>
            <v-tab-item>
              <v-form>
                <p>This form will import staff from an existing uber instance.</p>
                <p>Enter your uber login:</p>
                <v-text-field label="Email" v-model="email" outlined></v-text-field>
                <v-text-field label="Password" v-model="password" type="password" outlined></v-text-field>
                <v-text-field label="Uber Base URL" v-model="uber_url" placeholder="https://super2020.reggie.magfest.org" outlined></v-text-field>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn outlined type="submit" @click.prevent="submitRequest">Import</v-btn>
                </v-card-actions>
              </v-form>
            </v-tab-item>
            <v-tab>
              CSV
            </v-tab>
            <v-tab-item>
              <v-form>
                <p>Import data from a CSV file</p>
                <v-select label="CSV Type" outlined v-model="csv_type" :items="csv_types"></v-select>
                <v-file-input label="CSV Upload" v-model="files" accept=".csv" show-size outlined></v-file-input>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn outlined type="submit" @click.prevent="importCSV">Import</v-btn>
                </v-card-actions>
              </v-form>
            </v-tab-item>
            <v-tab>
              Mock Data
            </v-tab>
            <v-tab-item>
              <v-form>
                <p>This tool generates testing data.</p>
                <p>How much test data should be generated?</p>
                <v-text-field label="Number of Attendees" v-model="attendees" outlined></v-text-field>
                <v-text-field label="Number of Staffers" v-model="staffers" outlined></v-text-field>
                <v-text-field label="Number of Departments" v-model="departments" outlined></v-text-field>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn outlined type="submit" @click.prevent="generateMock">Generate</v-btn>
                </v-card-actions>
              </v-form>
            </v-tab-item>
          </v-tabs>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'DataImporter',
  components: {
  },
  data: () => ({
    loading: false,
    email: '',
    password: '',
    uber_url: '',
    attendees: 50000,
    departments: 50,
    staffers: 2000,
    csv_type: 'Attendees',
    files: [],
    csv_types: [
      'Attendees',
      'Departments',
    ],
  }),
  computed: {
    ...mapGetters([
      'event',
    ]),
  },
  mounted() {
  },
  methods: {
    submitRequest() {
      this.loading = true;
      const self = this;
      this.post('/api/importer/uber_staff', {
        email: this.email,
        password: this.password,
        uber_url: this.uber_url,
        event: this.event.id,
      }).then((resp) => {
        if (resp.success) {
          self.$store.commit('open_snackbar', `${resp.num_staff} Staff imported successfully!`);
          self.loading = false;
        } else {
          self.$store.commit('open_snackbar', 'Failed to import staff.');
          self.loading = false;
        }
      }).catch(() => {
        self.$store.commit('open_snackbar', 'Network error while importing staff.');
        self.loading = false;
      });
    },
    importCSV() {

    },
    generateMock() {

    },
  },
};
</script>
