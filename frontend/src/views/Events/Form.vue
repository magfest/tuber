<template>
     <v-card :loading="loading">
        <v-card-title class="headline grey lighten-2" primary-title>
            Edit Event
        </v-card-title>
        <br>
        <v-card-text>
            <v-form>
                <p>Describe your event:</p>
                <v-text-field label="Name" v-model="value.name" outlined></v-text-field>
                <v-text-field label="Description" v-model="value.description" outlined></v-text-field>
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
  name: 'event-form',
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
      }),
    },
  },
  methods: {
    save_data() {
      this.loading = true;
      this.save('events', this.value).then(() => {
        this.loading = false;
        this.$emit('saved');
        this.$emit('input');
      }).catch(() => {
        this.loading = false;
        this.notify('Failed to save event.');
      });
    },
  },
};
</script>
