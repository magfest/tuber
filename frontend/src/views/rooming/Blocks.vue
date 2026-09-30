<template>
  <div class="card">
    <div class="flex justify-content-between align-items-center flex-wrap gap-2">
      <h3 class="mt-0 mb-0">Rooming Blocks</h3>
      <router-link to="/rooming/settings" class="settings-link">
        <i class="pi pi-cog" /> Manage blocks
      </router-link>
    </div>
    <p v-if="loaded && !blocks.length">
      There are no blocks yet. Create them under Rooming → Settings, then come back to place people.
    </p>

    <tuber-table ref="table" url="/api/event/<event>/hotel/attendees" tableTitle="" formTitle="Request"
                 :envelope="true" routeSync="b" :parameters="parameters" :filters="filters"
                 :showActions="false" :showAdd="false" :onSelect="setSelection">
      <template #controls>
        <div class="flex gap-2 align-items-center flex-wrap">
          <Dropdown v-model="block" :options="filterOptions" optionLabel="label" optionValue="value"
                    placeholder="All requests" title="Which requests to list" />
          <div class="field-checkbox mb-0">
            <Checkbox inputId="everyone" v-model="everyone" :binary="true" />
            <label for="everyone" title="Also list declined requests and people who have not asked for any nights">
              Show everyone
            </label>
          </div>
          <Dropdown v-model="target" :options="targetOptions" optionLabel="label" optionValue="value"
                    placeholder="Move selected to…" :disabled="!selection.length" />
          <Button :label="moveLabel" icon="pi pi-arrow-right"
                  :disabled="!selection.length || target === null" :loading="moving"
                  @click="moveSelected" />
        </div>
      </template>
      <template #columns>
        <Column selectionMode="multiple" headerStyle="width: 3em"></Column>
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
        <Column field="status" header="Status" :sortable="true">
          <template #body="slotProps">
            <Tag v-if="slotProps.data.declined" severity="danger" value="Declined" />
            <Tag v-else-if="slotProps.data.completed" severity="success" value="Complete" />
            <Tag v-else severity="warning" value="Incomplete" />
          </template>
        </Column>
        <Column field="notes" header="Notes" :sortable="true" :showFilterMenu="false">
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" @keydown.enter="filterCallback()"
                       class="p-column-filter" placeholder="Search notes" />
          </template>
        </Column>
        <Column field="admin_notes" header="Admin Notes" :sortable="true" :showFilterMenu="false">
          <template #body="slotProps">
            <inline-note :modelValue="slotProps.data.admin_notes || ''"
                         @update:modelValue="slotProps.data.admin_notes = $event"
                         :save="(text) => saveAdminNote(slotProps.data, text)" />
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" @keydown.enter="filterCallback()"
                       class="p-column-filter" placeholder="Search admin notes" />
          </template>
        </Column>
        <Column field="hotel_block" header="Block" :sortable="true" style="width: 14rem">
          <template #body="slotProps">
            <Dropdown :modelValue="slotProps.data.hotel_block" :options="blocks"
                      optionLabel="name" optionValue="id" placeholder="No block" :showClear="true"
                      class="p-inputtext-sm w-full"
                      @update:modelValue="setBlock(slotProps.data, $event)" />
          </template>
        </Column>
      </template>
    </tuber-table>
  </div>
</template>

<style scoped>
.settings-link {
  color: var(--primary-color, #2196f3);
  text-decoration: none;
}
.settings-link:hover {
  text-decoration: underline;
}
</style>

<script>
import { mapGetters } from 'vuex'
import { FilterMatchMode } from 'primevue/api'
import { get, post } from '../../lib/rest'
import TuberTable from '../../components/TuberTable.vue'
import AttendeeName from '../../components/rooming/modals/AttendeeName.vue'
import InlineNote from '../../components/rooming/InlineNote.vue'
import { saveRequestAdminNote } from '../../lib/adminNotes'

export default {
  name: 'RoomBlocks',
  components: {
    TuberTable,
    AttendeeName,
    InlineNote
  },
  data: () => ({
    blocks: [],
    loaded: false,
    // null = every block, -1 = no block yet, otherwise a block id.
    block: null,
    everyone: false,
    selection: [],
    target: null,
    moving: false,
    filters: {
      name: { value: null, matchMode: FilterMatchMode.CONTAINS },
      departments: { value: null, matchMode: FilterMatchMode.CONTAINS },
      notes: { value: null, matchMode: FilterMatchMode.CONTAINS },
      admin_notes: { value: null, matchMode: FilterMatchMode.CONTAINS }
    }
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    filterOptions () {
      return [
        { label: 'All requests', value: null },
        { label: 'No block yet', value: -1 }
      ].concat(this.blocks.map((x) => ({ label: x.name, value: x.id })))
    },
    targetOptions () {
      return this.blocks.map((x) => ({ label: x.name, value: x.id }))
        .concat([{ label: 'No block', value: -1 }])
    },
    parameters () {
      // "active" = not declined and wants at least one night; the people who
      // actually need a block. The backend treats block=-1 as "no block".
      const params = { filter: this.everyone ? 'all' : 'active' }
      if (this.block !== null) {
        params.block = this.block
      }
      return params
    },
    moveLabel () {
      return this.selection.length ? 'Move ' + this.selection.length + ' selected' : 'Move selected'
    }
  },
  mounted () {
    const fromQuery = parseInt(this.$route.query.block)
    if (!isNaN(fromQuery)) {
      this.block = fromQuery
    }
    this.loadBlocks()
    window.addEventListener('detailmodal-changed', this.reloadTable)
  },
  unmounted () {
    window.removeEventListener('detailmodal-changed', this.reloadTable)
  },
  methods: {
    plural (count, word) {
      return count + ' ' + word + (count === 1 ? '' : 's')
    },
    async loadBlocks () {
      if (!this.event) {
        return
      }
      this.blocks = await get('/api/event/' + this.event.id + '/hotel_room_block', { sort: 'name' })
      this.loaded = true
    },
    reloadTable () {
      if (this.$refs.table) {
        this.$refs.table.reload()
      }
    },
    setSelection (selection) {
      this.selection = selection
    },
    saveAdminNote (row, text) {
      return saveRequestAdminNote(this.event.id, row.request_id, text)
    },
    async setBlock (row, blockId) {
      try {
        await post('/api/event/' + this.event.id + '/hotel/block_assignments',
          { updates: [{ id: row.request_id, hotel_block: blockId === null ? -1 : blockId }] })
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Could not change block', life: 3000 })
        return
      }
      row.hotel_block = blockId
      // When the list is narrowed to one block the row no longer belongs here.
      if (this.block !== null) {
        this.reloadTable()
      }
    },
    async moveSelected () {
      if (!this.selection.length || this.target === null) {
        return
      }
      const updates = this.selection.map((row) => ({ id: row.request_id, hotel_block: this.target }))
      this.moving = true
      try {
        await post('/api/event/' + this.event.id + '/hotel/block_assignments', { updates })
        this.$toast.add({ severity: 'success', summary: 'Moved ' + this.plural(updates.length, 'request'), life: 2000 })
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Move Failed', life: 3000 })
      }
      this.moving = false
      this.reloadTable()
    }
  },
  watch: {
    event () {
      this.loadBlocks()
    },
    block (value) {
      const query = Object.assign({}, this.$route.query)
      if (value === null) {
        delete query.block
      } else {
        query.block = String(value)
      }
      if (JSON.stringify(query) !== JSON.stringify(this.$route.query)) {
        this.$router.replace({ query })
      }
    }
  }
}
</script>
