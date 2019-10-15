<template>
  <div>
    <div>
      <br>
      <v-card max-width="700" :raised="true" class="mx-auto" :loading="loading">
        <v-card-title>Staff Import</v-card-title>
        <v-card-text>
          <v-form>
            <p>This form will import staff from an existing uber instance.</p>
            <p>Enter your uber login:</p>
            <v-text-field label="Email" v-model="email" outlined></v-text-field>
            <v-text-field label="Password" v-model="password" type="password" outlined></v-text-field>
            <v-text-field label="Uber Base URL" v-model="uber_url" placeholder="https://super2020.reggie.magfest.org" outlined></v-text-field>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn outlined type="submit" @click="submitRequest">Submit</v-btn>
            </v-card-actions>
          </v-form>
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
  name: 'StaffImporter',
  components: {
  },
  data: () => ({
    loading: false,
    email: '',
    password: '',
    uber_url: '',
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
  },
};
</script>
