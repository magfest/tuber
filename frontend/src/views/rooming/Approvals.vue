<template>
  <div>
      <Dropdown v-model="departmentID" :options="departments" optionLabel="name" optionValue="id" />
      <approval v-if="departmentID" :departmentID="departmentID" />
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex'
import { get } from '@/lib/rest'
import Approval from './Approval.vue'

export default {
  name: 'RoomApprovals',
  components: {
    Approval
  },
  data: () => ({
    departmentID: null,
    departments: []
  }),
  computed: {
    ...mapGetters([
      'event'
    ])
  },
  mounted () {
  },
  methods: {
    async load () {
      const depts = await get('/api/event/' + this.event.id + '/department')
      if (depts) {
        this.departments = depts
        this.departmentID = this.departments[0].id
      }
    }
  },
  watch: {
    event () {
      this.load()
    }
  }
}
</script>
