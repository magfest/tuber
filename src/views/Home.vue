<template>
  <div>
    <v-container>
      <v-row>
        <v-col>
          <v-card max-width="350" :raised="true" class="mx-auto">
            <v-card-title>Hotel Request Completion</v-card-title>
            <v-card-text>
              <apexchart type="donut" width="320" :series="series || []" :options="{legend: {show: false}, labels: ['completed', 'pending']}"></apexchart>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'Home',
  data() {
    return {
    };
  },
  computed: {
    ...mapGetters([
      'event',
      'user',
    ]),
  },
  asyncComputed: {
    series() {
      const self = this;
      return new Promise((resolve) => {
        self.get('/api/hotels/statistics', { event: self.event.id }).then((resp) => {
          resolve([resp.num_requests, resp.num_badges - resp.num_requests]);
        });
      });
    },
  },
};
</script>
