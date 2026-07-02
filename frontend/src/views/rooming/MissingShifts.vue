<template>
  <div class="card">
    <h3>Missing Shifts</h3>
    <p>
      These people have requested a restricted room night but do not have a shift
      overlapping that night's shift time window. They will not be approved
      automatically. From here you can manually approve or assign the night anyway,
      or export the list to ask people to sign up for more shifts.
    </p>
    <DataTable :value="rows" :loading="loading" :paginator="rows.length > 25" :rows="25"
               v-model:filters="filters" :globalFilterFields="['name', 'departments', 'night.name']">
      <template #header>
        <div class="table-header">
          <span class="p-input-icon-left">
            <i class="pi pi-search" />
            <InputText v-model="filters['global'].value" placeholder="Search" />
          </span>
          <Button label="Export CSV" icon="pi pi-download" @click="exportCsv" />
        </div>
      </template>
      <template #empty>
        Nobody is missing a shift for the nights they requested.
      </template>
      <Column field="name" header="Name" :sortable="true"></Column>
      <Column field="departments" header="Departments">
        <template #body="slotProps">
          {{ slotProps.data.departments.join(', ') }}
        </template>
      </Column>
      <Column field="night.date" header="Night" :sortable="true">
        <template #body="slotProps">
          {{ slotProps.data.night.name }} ({{ slotProps.data.night.date }})
          <Tag v-if="slotProps.data.night.restriction_type" :value="slotProps.data.night.restriction_type"
               severity="warning" class="ml-2" />
        </template>
      </Column>
      <Column header="Requested">
        <template #body="slotProps">
          <i class="pi" :class="slotProps.data.night.requested ? 'pi-check flag-on' : 'pi-times flag-off'" />
        </template>
      </Column>
      <Column header="Approved">
        <template #body="slotProps">
          <InputSwitch :modelValue="slotProps.data.night.approved" :disabled="slotProps.data.busy"
                       @update:modelValue="toggleApproval(slotProps.data, $event)" />
        </template>
      </Column>
      <Column header="Assigned">
        <template #body="slotProps">
          <InputSwitch :modelValue="slotProps.data.night.assigned" :disabled="slotProps.data.busy"
                       @update:modelValue="toggleAssignment(slotProps.data, $event)" />
        </template>
      </Column>
      <Column header="Details">
        <template #body="slotProps">
          <Button icon="pi pi-calendar" class="p-button-rounded p-button-text"
                  @click="showDetails(slotProps.data)" />
        </template>
      </Column>
    </DataTable>

    <missing-shift-details v-model:visible="detailsVisible" :badge-id="detailsBadge" />
  </div>
</template>

<style scoped>
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.flag-on { color: var(--green-600, #16a34a); }
.flag-off { color: var(--surface-400, #ced4da); }
</style>

<script>
import { mapGetters } from 'vuex'
import { FilterMatchMode } from 'primevue/api'
import InputSwitch from 'primevue/inputswitch'
import { get, post } from '../../lib/rest'
import MissingShiftDetails from '../../components/rooming/missing/MissingShiftDetails.vue'

export default {
  name: 'RoomMissingShifts',
  components: {
    InputSwitch,
    MissingShiftDetails
  },
  data: () => ({
    rows: [],
    loading: false,
    detailsVisible: false,
    detailsBadge: null,
    filters: {
      global: { value: null, matchMode: FilterMatchMode.CONTAINS }
    }
  }),
  computed: {
    ...mapGetters([
      'event'
    ])
  },
  mounted () {
    this.load()
  },
  methods: {
    async load () {
      this.loading = true
      const badges = await get('/api/event/' + this.event.id + '/hotel/missing_shifts')
      // One row per person and missing night, so each night can be
      // approved/assigned independently.
      this.rows = badges.flatMap((badge) => badge.missing_nights.map((night) => ({
        badgeId: badge.id,
        name: badge.name,
        email: badge.email,
        departments: badge.departments,
        night,
        busy: false
      })))
      this.loading = false
    },
    async toggleApproval (row, value) {
      row.busy = true
      try {
        const res = await post('/api/event/' + this.event.id + '/hotel/missing_shifts/approve',
          { badge: row.badgeId, room_night: row.night.id, approved: value })
        row.night.approved = res.approved
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Update Failed', detail: 'Could not update approval.', life: 3000 })
      }
      row.busy = false
    },
    async toggleAssignment (row, value) {
      row.busy = true
      try {
        const res = await post('/api/event/' + this.event.id + '/hotel/missing_shifts/assign',
          { badge: row.badgeId, room_night: row.night.id, assigned: value })
        row.night.assigned = res.assigned
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Update Failed', detail: 'Could not update assignment.', life: 3000 })
      }
      row.busy = false
    },
    showDetails (row) {
      this.detailsBadge = row.badgeId
      this.detailsVisible = true
    },
    async exportCsv () {
      const resp = await fetch('/api/event/' + this.event.id + '/hotel/missing_shifts/export',
        { credentials: 'include' })
      if (!resp.ok) {
        this.$toast.add({ severity: 'error', summary: 'Export Failed', life: 3000 })
        return
      }
      const url = URL.createObjectURL(await resp.blob())
      const link = document.createElement('a')
      link.href = url
      link.download = 'missing_shifts.csv'
      link.click()
      URL.revokeObjectURL(url)
    }
  },
  watch: {
    event () {
      this.load()
    }
  }
}
</script>
