<template>
  <div class="card">
    <h3>Missing Shifts</h3>
    <p>
      People with restricted room nights are approved automatically only when a shift
      overlaps the night's shift window. Use the details view to inspect someone's
      schedule and change their nights, or export the missing list to ask people to
      sign up for more shifts.
    </p>
    <DataTable :value="rows" :loading="loading" :paginator="rows.length > 25" :rows="25"
               v-model:filters="filters" :globalFilterFields="['name', 'departments']">
      <template #header>
        <div class="table-header">
          <SelectButton v-model="mode" :options="modes" optionLabel="label" optionValue="value"
                        :allowEmpty="false" @change="load" />
          <span class="p-input-icon-left">
            <i class="pi pi-search" />
            <InputText v-model="filters['global'].value" placeholder="Search" />
          </span>
          <Button label="Export Missing (CSV)" icon="pi pi-download" @click="exportCsv" />
        </div>
      </template>
      <template #empty>
        {{ mode === 'missing' ? 'Nobody is missing a shift for the nights they requested.' : 'No results.' }}
      </template>
      <Column field="name" header="Name" :sortable="true"></Column>
      <Column field="departments" header="Departments">
        <template #body="slotProps">
          {{ slotProps.data.departments.join(', ') }}
        </template>
      </Column>
      <Column field="requested_nights" header="Nights Requested" :sortable="true"></Column>
      <Column field="assigned_nights" header="Nights Assigned" :sortable="true"></Column>
      <Column header="Missing Shifts">
        <template #body="slotProps">
          <Tag v-for="night in slotProps.data.missing_nights" :key="night.id"
               :severity="night.approved || night.assigned ? 'success' : 'warning'"
               :value="nightLabel(night)" class="mr-2 mb-1" />
        </template>
      </Column>
      <Column header="Details">
        <template #body="slotProps">
          <Button icon="pi pi-calendar" class="p-button-rounded p-button-text"
                  @click="showDetails(slotProps.data)" />
        </template>
      </Column>
    </DataTable>

    <missing-shift-details v-model:visible="detailsVisible" :badge-id="detailsBadge"
                           @changed="dirty = true" />
  </div>
</template>

<style scoped>
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}
</style>

<script>
import { mapGetters } from 'vuex'
import { FilterMatchMode } from 'primevue/api'
import SelectButton from 'primevue/selectbutton'
import { get } from '../../lib/rest'
import MissingShiftDetails from '../../components/rooming/missing/MissingShiftDetails.vue'

export default {
  name: 'RoomMissingShifts',
  components: {
    SelectButton,
    MissingShiftDetails
  },
  data: () => ({
    rows: [],
    loading: false,
    detailsVisible: false,
    detailsBadge: null,
    dirty: false,
    mode: 'missing',
    modes: [
      { label: 'Missing Shifts', value: 'missing' },
      { label: 'With Requests', value: 'requested' },
      { label: 'With Rooms', value: 'assigned' },
      { label: 'Everyone', value: 'all' }
    ],
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
      this.rows = await get('/api/event/' + this.event.id + '/hotel/missing_shifts',
        { filter: this.mode })
      this.loading = false
    },
    nightLabel (night) {
      let label = night.name
      if (night.date) {
        label += ' (' + night.date + ')'
      }
      if (night.approved) {
        label += ' — approved'
      }
      if (night.assigned) {
        label += ' — assigned'
      }
      return label
    },
    showDetails (row) {
      this.detailsBadge = row.id
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
    },
    detailsVisible (val) {
      // Changes made in the modal affect the flags (and possibly which rows
      // still qualify), so refresh the table once the modal closes.
      if (!val && this.dirty) {
        this.dirty = false
        this.load()
      }
    }
  }
}
</script>
