<template>
    <v-card :loading="loading">
        <v-card-title class="headline grey lighten-2" primary-title>
            Edit Email Source
        </v-card-title>
        <br>
        <v-card-text>
            <v-form>
                <v-text-field label="Name" v-model="value.name"></v-text-field>
                <v-text-field label="Description" v-model="value.description"></v-text-field>
                <v-text-field label="From Address" v-model="value.address"></v-text-field>
                <v-text-field label="SES Access Key" v-model="value.ses_access_key"></v-text-field>
                <v-text-field label="SES Secret Key" v-model="value.ses_secret_key"></v-text-field>
                <v-text-field label="AWS Region" v-model="value.region"></v-text-field>
                <v-checkbox label="Active" v-model="value.active"></v-checkbox>
            </v-form>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn left @click="$emit('input')">Close</v-btn>
            <v-btn color="primary" text @click="save_data">Save</v-btn>
        </v-card-actions>
    </v-card>
</template>

<script>
export default {
  name: 'emailsource-form',
  components: {
  },
  data: () => ({
    loading: false,
  }),
  props: {
    value: {
      default: () => ({
        name: '',
        description: '',
        address: '',
        ses_access_key: '',
        ses_secret_key: '',
        region: '',
        active: false,
      }),
    },
  },
  methods: {
    save_data() {
      this.loading = true;
      this.save('email_sources', this.value).then(() => {
        this.loading = false;
        this.$emit('saved');
        this.$emit('input');
      }).catch(() => {
        this.loading = false;
        this.notify('Failed to save email source.');
      });
    },
  },
};
</script>
