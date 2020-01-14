<template>
  <v-tab-item>
    <v-form>
      <p>This form will import staff from an existing uber instance.</p>
      <p>Enter your uber login:</p>
      <v-text-field label="Email" v-model="email" outlined/>
      <v-text-field label="Password" v-model="password" type="password" outlined/>
      <v-text-field label="Uber Base URL" v-model="uber_url" placeholder="https://super2020.reggie.magfest.org" outlined/>
      <v-card-actions>
        <v-spacer/>
        <v-btn outlined type="submit" @click.prevent="submitRequest">Import</v-btn>
      </v-card-actions>
    </v-form>
  </v-tab-item>
</template>

<script>
export default {
  name: 'LoginFromUber',
  data() {
    return {
      email: '',
      password: '',
      uber_url: '',
    };
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
          self.$store.commit('open_snackbar', 'Import started successfully. It will complete in the background.');
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

<style scoped>

</style>
