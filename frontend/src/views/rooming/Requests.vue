<template>
  <div class="card">
    <tuber-table ref="table" :url="'/api/event/<event>/hotel/attendees'" tableTitle="Requests"
                 formTitle="Request" :envelope="true" routeSync="a" :modes="modes"
                 :parameters="parameters" :filters="filters" :showActions="false" :showAdd="false">
      <template #controls>
        <div class="flex gap-2 align-items-center">
          <Dropdown v-model="block" :options="blockOptions" optionLabel="name" optionValue="id"
                    placeholder="All Blocks" :showClear="true" />
          <Button label="Export CSV" icon="pi pi-download" @click="exportCsv" />
        </div>
      </template>
      <template #columns>
        <Column field="name" header="Name" :sortable="true" :showFilterMenu="false">
          <template #body="slotProps">
            <attendee-name :badge-id="slotProps.data.id" :name="slotProps.data.name" />
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" @keydown.enter="filterCallback()"
                       class="p-column-filter" placeholder="Search name" />
          </template>
        </Column>
        <Column field="departments" header="Departments" :sortable="true" :showFilterMenu="false">
          <template #body="slotProps">
            {{ slotProps.data.departments.join(', ') }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" @keydown.enter="filterCallback()"
                       class="p-column-filter" placeholder="Search department" />
          </template>
        </Column>
        <Column field="hotel_block" header="Block" :sortable="true">
          <template #body="slotProps">
            <Dropdown :modelValue="slotProps.data.hotel_block" :options="blockOptions"
                      optionLabel="name" optionValue="id" placeholder="No block" :showClear="true"
                      class="p-inputtext-sm"
                      @update:modelValue="setBlock(slotProps.data, $event)" />
          </template>
        </Column>
        <Column field="status" header="Status" :sortable="true">
          <template #body="slotProps">
            <Tag v-if="slotProps.data.declined" severity="danger" value="Declined" />
            <Tag v-else-if="slotProps.data.completed" severity="success" value="Complete" />
            <Tag v-else severity="warning" value="Incomplete" />
          </template>
        </Column>
        <Column field="requested_nights" header="Requested" :sortable="true"></Column>
        <Column field="approved_nights" header="Approved" :sortable="true"></Column>
        <Column field="assigned_nights" header="Assigned" :sortable="true"></Column>
        <Column field="notes" header="Notes" :sortable="true" :showFilterMenu="false">
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" @keydown.enter="filterCallback()"
                       class="p-column-filter" placeholder="Search notes" />
          </template>
        </Column>
        <Column field="missing" header="Missing Shifts" :sortable="true">
          <template #body="slotProps">
            <Tag v-for="night in slotProps.data.missing_nights" :key="night.id"
                 :severity="night.approved || night.assigned ? 'warning' : 'danger'"
                 :value="nightLabel(night)" class="mr-1 mb-1" />
          </template>
        </Column>
      </template>
    </tuber-table>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { FilterMatchMode } from 'primevue/api'
import { get, post } from '../../lib/rest'
import TuberTable from '../../components/TuberTable.vue'
import AttendeeName from '../../components/rooming/modals/AttendeeName.vue'

export default {
  name: 'RoomRequests',
  components: {
    TuberTable,
    AttendeeName
  },
  data: () => ({
    block: null,
    blocks: [],
    modes: [
      { label: 'All', value: 'all' },
      { label: 'Incomplete', value: 'incomplete' },
      { label: 'Declined', value: 'declined' },
      { label: 'Missing Shifts', value: 'missing_shifts' },
      { label: 'Unassigned', value: 'unassigned_approved' }
    ],
    filters: {
      name: { value: null, matchMode: FilterMatchMode.CONTAINS },
      departments: { value: null, matchMode: FilterMatchMode.CONTAINS },
      notes: { value: null, matchMode: FilterMatchMode.CONTAINS }
    }
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    blockOptions () {
      return this.blocks
    },
    parameters () {
      const params = {}
      if (this.block) {
        params.block = this.block
      }
      return params
    }
  },
  mounted () {
    this.load()
    if (this.$route.query.block) {
      this.block = parseInt(this.$route.query.block) || null
    }
    window.addEventListener('detailmodal-changed', this.reloadTable)
  },
  unmounted () {
    window.removeEventListener('detailmodal-changed', this.reloadTable)
  },
  methods: {
    async load () {
      this.blocks = await get('/api/event/' + this.event.id + '/hotel_room_block', { sort: 'name' })
    },
    reloadTable () {
      if (this.$refs.table) {
        this.$refs.table.load()
      }
    },
    nightLabel (night) {
      let label = night.name
      if (night.mode === 'shift_hours') {
        label += ' (' + night.hours_assigned + '/' + night.hours_required + 'h)'
      }
      if (night.approved) {
        label += ' — approved'
      }
      if (night.assigned) {
        label += ' — assigned'
      }
      return label
    },
    async setBlock (row, blockId) {
      await post('/api/event/' + this.event.id + '/hotel/block_assignments',
        { updates: [{ id: row.request_id, hotel_block: blockId === null ? -1 : blockId }] })
      row.hotel_block = blockId
    },
    async exportCsv () {
      const mode = this.$refs.table ? this.$refs.table.mode : 'missing_shifts'
      const resp = await fetch('/api/event/' + this.event.id + '/hotel/attendees/export?filter=' + mode,
        { credentials: 'include' })
      if (!resp.ok) {
        this.$toast.add({ severity: 'error', summary: 'Export Failed', life: 3000 })
        return
      }
      const url = URL.createObjectURL(await resp.blob())
      const link = document.createElement('a')
      link.href = url
      link.download = mode + '_attendees.csv'
      link.click()
      URL.revokeObjectURL(url)
    }
  },
  watch: {
    event () {
      this.load()
    },
    block (value) {
      const query = Object.assign({}, this.$route.query)
      if (value) {
        query.block = String(value)
      } else {
        delete query.block
      }
      this.$router.replace({ query })
    }
  }
}
</script>
