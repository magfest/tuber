<template>
  <div class="card">
    <Toast />
    <div class="flex justify-content-between align-items-center flex-wrap gap-2">
      <div>
        <h3 class="mt-0 mb-0">Uber Inventory</h3>
        <small class="hint">
          Which Uber inventory block and partition each room exports into.
          A room with no inventory is not exported.
        </small>
      </div>
      <div class="flex gap-2 align-items-center">
        <small class="hint" v-if="imported">Lists imported {{ formatTimestamp(imported) }}</small>
        <small class="hint" v-else>Nothing imported from Uber yet</small>
        <Button label="Import from Uber" icon="pi pi-cloud-download" class="p-button-outlined"
                title="Fetch the current inventory blocks and partitions from Uber"
                :loading="importing" @click="importOptions" />
        <span class="p-input-icon-left">
          <i class="pi pi-search" />
          <InputText v-model="search" placeholder="Room or roommate name" @change="onFilter" />
        </span>
      </div>
    </div>
    <div class="filter-bar">
      <Dropdown v-model="block" :options="blockOptions" optionLabel="label" optionValue="value"
                placeholder="Any block" :showClear="block !== null" title="Filter by hotel block" />
      <Dropdown v-model="inventoryFilter" :options="inventoryFilterOptions" optionLabel="label"
                optionValue="value" placeholder="Any inventory" :showClear="inventoryFilter !== null"
                title="Filter by Uber inventory" />
      <Dropdown v-model="partitionFilter" :options="partitionFilterOptions" optionLabel="label"
                optionValue="value" placeholder="Any partition" :showClear="partitionFilter !== null"
                title="Filter by Uber partition" />
    </div>
    <!-- Always shown, so ticking a row does not shift the table under the cursor. -->
    <div class="bulk-bar">
      <strong>{{ selection.length }} selected</strong>
      <Dropdown v-model="bulkInventory" :options="inventoryOptions" optionLabel="label" optionValue="value"
                placeholder="Inventory…" :showClear="true" :filter="true" class="p-inputtext-sm" />
      <Dropdown v-model="bulkPartition" :options="partitionOptionsFor(bulkInventory)" optionLabel="label"
                optionValue="value" placeholder="Partition…" :showClear="true" :filter="true"
                class="p-inputtext-sm" />
      <Button label="Apply to selected" icon="pi pi-check" class="p-button-sm"
              :disabled="!selection.length || (!bulkInventory && !bulkPartition)" :loading="applying"
              @click="applyBulk" />
      <Button label="Clear on selected" icon="pi pi-times" class="p-button-sm p-button-outlined p-button-danger"
              title="Remove the inventory and partition from the selected rooms"
              :disabled="!selection.length" :loading="applying" @click="clearBulk" />
    </div>

    <DataTable :value="rooms" :loading="loading" dataKey="id" class="p-datatable-sm"
               :paginator="true" :rows="25" :lazy="true" :totalRecords="count"
               v-model:selection="selection"
               @page="onPage($event)" @sort="onSort($event)"
               sortField="name" :sortOrder="1">
      <Column selectionMode="multiple" style="width: 3rem" />
      <Column field="name" header="Room" :sortable="true">
        <template #body="slotProps">
          <room-name :room-id="slotProps.data.id" :name="slotProps.data.name" />
        </template>
      </Column>
      <Column header="Occupants">
        <template #body="slotProps">
          <div v-for="mate in occupants(slotProps.data)" :key="mate.id" class="occupant-line">
            <attendee-name :badge-id="mate.id" :name="mate.name" />
          </div>
          <span v-if="!occupants(slotProps.data).length" class="hint">Empty</span>
        </template>
      </Column>
      <Column header="Hotel Notes">
        <template #body="slotProps">
          <inline-note compact :modelValue="slotProps.data.notes || ''" label="note for the hotel"
                       placeholder="Add hotel note"
                       @update:modelValue="slotProps.data.notes = $event"
                       :save="(text) => saveHotelNote(slotProps.data, text)" />
        </template>
      </Column>
      <Column header="Inventory" style="width: 22rem">
        <template #body="slotProps">
          <Dropdown :modelValue="slotProps.data.uber_inventory_id || null"
                    :options="inventoryOptionsFor(slotProps.data)" optionLabel="label" optionValue="value"
                    placeholder="Not set" :showClear="true" :filter="true"
                    class="p-inputtext-sm w-full"
                    @update:modelValue="setField(slotProps.data, 'uber_inventory_id', $event)" />
        </template>
      </Column>
      <Column header="Partition" style="width: 18rem">
        <template #body="slotProps">
          <Dropdown :modelValue="slotProps.data.uber_partition_id || null"
                    :options="partitionOptionsFor(slotProps.data.uber_inventory_id, slotProps.data.uber_partition_id)"
                    optionLabel="label" optionValue="value" placeholder="No partition"
                    :showClear="true" :filter="true" class="p-inputtext-sm w-full"
                    @update:modelValue="setField(slotProps.data, 'uber_partition_id', $event)" />
          <small class="warning" v-if="partitionMismatch(slotProps.data)">
            <i class="pi pi-exclamation-triangle" /> Not a partition of this inventory
          </small>
        </template>
      </Column>
      <Column header="Uber" style="width: 8rem">
        <template #body="slotProps">
          <Tag v-if="!slotProps.data.uber_inventory_id" severity="danger" value="No inventory"
               title="The export skips this room until it has an inventory" />
          <Tag v-else-if="slotProps.data.uber_id" severity="success" value="Exported"
               title="Changes here are sent on the next export" />
          <Tag v-else severity="info" value="Not exported" />
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<style scoped>
.filter-bar, .bulk-bar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
  margin: 0.4rem 0 0.6rem 0;
}
.filter-bar .p-dropdown, .bulk-bar .p-dropdown {
  min-width: 11rem;
}
.bulk-bar {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--surface-border, #dee2e6);
  border-radius: 6px;
}
.occupant-line {
  margin: 1px 0;
}
.hint {
  color: var(--text-color-secondary, #6c757d);
}
.warning {
  display: block;
  margin-top: 0.2rem;
  color: var(--orange-500, #f59e0b);
}
</style>

<script>
import { mapGetters } from 'vuex'
import { get, post, patch } from '../../lib/rest'
import RoomName from '../../components/rooming/modals/RoomName.vue'
import AttendeeName from '../../components/rooming/modals/AttendeeName.vue'
import InlineNote from '../../components/rooming/InlineNote.vue'

export default {
  name: 'UberInventory',
  components: {
    RoomName,
    AttendeeName,
    InlineNote
  },
  data: () => ({
    rooms: [],
    count: 0,
    offset: 0,
    sort: 'name',
    order: 'asc',
    loading: false,
    loadSequence: 0,
    importing: false,
    applying: false,
    search: '',
    block: null,
    inventoryFilter: null,
    partitionFilter: null,
    blocks: [],
    roomDetails: {},
    inventory: [],
    partitions: [],
    imported: null,
    selection: [],
    bulkInventory: null,
    bulkPartition: null
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    blockOptions () {
      return [{ label: 'Any block', value: null }].concat(
        this.blocks.map((block) => ({ label: block.name, value: block.id })))
    },
    inventoryOptions () {
      return this.inventory.map((x) => ({ label: this.inventoryLabel(x), value: x.uber_id }))
    },
    inventoryFilterOptions () {
      return [{ label: 'No inventory', value: 'missing' }].concat(this.inventoryOptions)
    },
    partitionFilterOptions () {
      return [{ label: 'No partition', value: 'missing' }].concat(this.partitions.map((x) => ({ label: this.partitionLabel(x), value: x.uber_id })))
    }
  },
  mounted () {
    this.load()
    window.addEventListener('detailmodal-changed', this.loadRooms)
  },
  unmounted () {
    window.removeEventListener('detailmodal-changed', this.loadRooms)
  },
  methods: {
    async load () {
      if (!this.event) {
        return
      }
      this.blocks = await get('/api/event/' + this.event.id + '/hotel_room_block', { sort: 'name' })
      this.setOptions(await get('/api/event/' + this.event.id + '/uber/inventory_options'))
      await this.loadRooms()
    },
    setOptions (options) {
      this.inventory = options.inventory || []
      this.partitions = options.partitions || []
      this.imported = options.imported
    },
    async loadRooms () {
      if (!this.event) {
        return
      }
      // A filter change while a request is in flight must not let the old
      // response win.
      const sequence = ++this.loadSequence
      this.loading = true
      const params = {
        sort: this.sort,
        order: this.order,
        limit: 25,
        offset: this.offset
      }
      if (this.search) {
        params.search = this.search
      }
      if (this.block) {
        params.hotel_block = this.block
      }
      if (this.inventoryFilter) {
        params.uber_inventory = this.inventoryFilter
      }
      if (this.partitionFilter) {
        params.uber_partition = this.partitionFilter
      }
      try {
        const found = await get('/api/event/' + this.event.id + '/hotel/room_search', params)
        const ids = (found.hotel_rooms || []).map((x) => x.id)
        const details = ids.length
          ? await get('/api/event/' + this.event.id + '/hotel/room_details', { rooms: ids.join(',') })
          : {}
        if (sequence !== this.loadSequence) {
          return
        }
        this.rooms = found.hotel_rooms || []
        this.roomDetails = details
        this.count = found.count || 0
        this.selection = []
      } finally {
        if (sequence === this.loadSequence) {
          this.loading = false
        }
      }
    },
    async importOptions () {
      this.importing = true
      try {
        this.setOptions(await post('/api/event/' + this.event.id + '/uber/import_inventory'))
        this.$toast.add({
          severity: 'success',
          summary: 'Imported from Uber',
          detail: this.inventory.length + ' inventory blocks, ' + this.partitions.length + ' partitions',
          life: 3000
        })
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Import Failed', detail: e.message })
      }
      this.importing = false
    },
    inventoryLabel (item) {
      const label = item.hotel_name ? item.hotel_name + ' — ' + item.name : item.name
      return item.active ? label : label + ' (inactive)'
    },
    partitionLabel (item) {
      return item.active ? item.name : item.name + ' (inactive)'
    },
    occupants (room) {
      const details = this.roomDetails[room.id]
      return details
        ? Object.values(details.roommates).sort((a, b) => a.name.localeCompare(b.name))
        : []
    },
    // The hotel note is sent to Uber as the room's special requests.
    async saveHotelNote (room, text) {
      const saved = await patch('/api/event/' + this.event.id + '/hotel_room/' + room.id,
        { id: room.id, notes: text })
      return { notes: saved.notes }
    },
    // An id the last import no longer lists still has to show as selected.
    inventoryOptionsFor (room) {
      const id = room.uber_inventory_id
      return !id || this.inventory.some((x) => x.uber_id === id)
        ? this.inventoryOptions
        : this.inventoryOptions.concat([{ label: 'Unknown (' + id + ')', value: id }])
    },
    // Partitions of the given inventory, or all of them when it has none
    // (or no inventory is chosen), so the dropdown is never a dead end.
    partitionOptionsFor (inventoryId, current) {
      const matching = this.partitions.filter((x) => x.inventory_ids.includes(inventoryId))
      const shown = inventoryId && matching.length ? matching : this.partitions
      const options = shown.map((x) => ({ label: this.partitionLabel(x), value: x.uber_id }))
      if (current && !shown.some((x) => x.uber_id === current)) {
        const known = this.partitions.find((x) => x.uber_id === current)
        options.push({ label: known ? this.partitionLabel(known) : 'Unknown (' + current + ')', value: current })
      }
      return options
    },
    partitionMismatch (room) {
      const partition = this.partitions.find((x) => x.uber_id === room.uber_partition_id)
      const inventory = room.uber_inventory_id
      return Boolean(partition && inventory && !partition.inventory_ids.includes(inventory))
    },
    async setField (room, field, value) {
      const payload = { id: room.id }
      payload[field] = value || null
      try {
        await patch('/api/event/' + this.event.id + '/hotel_room/' + room.id, payload)
        room[field] = payload[field]
        this.$toast.add({ severity: 'success', summary: room.name + ' updated', life: 1500 })
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Update Failed', detail: e.message, life: 3000 })
      }
    },
    async patchSelected (changes) {
      this.applying = true
      const rooms = this.selection.slice()
      let failed = 0
      for (const room of rooms) {
        try {
          await patch('/api/event/' + this.event.id + '/hotel_room/' + room.id,
            Object.assign({ id: room.id }, changes))
          Object.assign(room, changes)
        } catch (e) {
          failed += 1
        }
      }
      this.applying = false
      this.$toast.add(failed
        ? { severity: 'error', summary: failed + ' of ' + rooms.length + ' rooms failed to update' }
        : { severity: 'success', summary: rooms.length + ' rooms updated', life: 2000 })
      this.loadRooms()
    },
    applyBulk () {
      const changes = {}
      if (this.bulkInventory) {
        changes.uber_inventory_id = this.bulkInventory
      }
      if (this.bulkPartition) {
        changes.uber_partition_id = this.bulkPartition
      }
      return this.patchSelected(changes)
    },
    clearBulk () {
      return this.patchSelected({ uber_inventory_id: null, uber_partition_id: null })
    },
    formatTimestamp (value) {
      const d = new Date(value)
      return isNaN(d.getTime()) ? '' : d.toLocaleString()
    },
    onFilter () {
      this.offset = 0
      this.loadRooms()
    },
    onPage (event) {
      this.offset = event.first
      this.loadRooms()
    },
    onSort (event) {
      this.sort = event.sortField
      this.order = event.sortOrder > 0 ? 'asc' : 'desc'
      this.onFilter()
    }
  },
  watch: {
    event () {
      this.load()
    },
    block () {
      this.onFilter()
    },
    inventoryFilter () {
      this.onFilter()
    },
    partitionFilter () {
      this.onFilter()
    }
  }
}
</script>
