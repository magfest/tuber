<template>
  <div class="card">
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <div class="flex justify-content-between align-items-center flex-wrap gap-2">
      <h3 class="mt-0 mb-0">Rooms</h3>
      <div class="flex gap-2 align-items-center">
        <Button label="Export Passkey CSV" icon="pi pi-download" class="p-button-outlined"
                title="Passkey-format CSV of all completed rooms" @click="exportPasskey" />
        <span class="p-input-icon-left">
          <i class="pi pi-search" />
          <InputText v-model="search" placeholder="Room or roommate name" @change="onFilter" />
        </span>
      </div>
    </div>
    <div class="filter-bar">
      <Dropdown v-model="block" :options="blockOptions" optionLabel="label" optionValue="value"
                placeholder="Any block" :showClear="block !== null" title="Filter by hotel block" />
      <Dropdown v-model="status" :options="statusOptions" optionLabel="label" optionValue="value"
                title="Filter by room status" />
      <Dropdown v-if="locations.length" v-model="location" :options="locationOptions"
                optionLabel="label" optionValue="value" placeholder="Any location"
                :showClear="location !== null" title="Filter by hotel location" />
    </div>

    <DataTable :value="rooms" :loading="loading" dataKey="id" class="p-datatable-sm"
               :paginator="true" :rows="25" :lazy="true" :totalRecords="count"
               @page="onPage($event)" @sort="onSort($event)"
               sortField="modified" :sortOrder="-1">
      <Column field="name" header="Name" :sortable="true">
        <template #body="slotProps">
          <room-name :room-id="slotProps.data.id" :name="slotProps.data.name" />
        </template>
      </Column>
      <Column field="hotel_block" header="Block">
        <template #body="slotProps">
          <Dropdown :modelValue="slotProps.data.hotel_block" :options="blocks"
                    optionLabel="name" optionValue="id" placeholder="No block" :showClear="true"
                    class="p-inputtext-sm"
                    @update:modelValue="setBlock(slotProps.data, $event)" />
        </template>
      </Column>
      <Column header="Occupants">
        <template #body="slotProps">
          <span v-for="(mate, index) in occupants(slotProps.data)" :key="mate.id">
            <template v-if="index > 0">, </template>
            <attendee-name :badge-id="mate.id" :name="mate.name" />
          </span>
          <span v-if="!occupants(slotProps.data).length" class="empty">Empty</span>
        </template>
      </Column>
      <Column header="Status">
        <template #body="slotProps">
          <Tag v-if="slotProps.data.completed" severity="success" value="Completed" class="mr-1" />
          <Tag v-else-if="slotProps.data.suggested" severity="warning" value="Suggested" class="mr-1" />
          <Tag v-else severity="info" value="In progress" class="mr-1" />
          <Tag v-if="slotProps.data.locked" value="Locked" class="mr-1" />
          <Tag v-if="issues(slotProps.data).length" severity="danger"
               :value="issues(slotProps.data).length + ' issue' + (issues(slotProps.data).length === 1 ? '' : 's')"
               :title="issues(slotProps.data).join('\n')" />
        </template>
      </Column>
      <Column field="modified" header="Last Modified" :sortable="true">
        <template #body="slotProps">
          {{ formatTimestamp(slotProps.data.modified) }}
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
  margin: 0.4rem 0 0.6rem 0;
}
.filter-bar .p-dropdown {
  min-width: 9rem;
}
.empty {
  color: var(--text-color-secondary, #6c757d);
  font-style: italic;
}
</style>

<script>
import { mapGetters } from 'vuex'
import { get, patch, download } from '../../lib/rest'
import AttendeeName from '../../components/rooming/modals/AttendeeName.vue'
import RoomName from '../../components/rooming/modals/RoomName.vue'

export default {
  name: 'RoomList',
  components: {
    AttendeeName,
    RoomName
  },
  data: () => ({
    rooms: [],
    count: 0,
    offset: 0,
    sort: 'modified',
    order: 'desc',
    loading: false,
    search: '',
    block: null,
    status: '',
    location: null,
    blocks: [],
    locations: [],
    roomDetails: {},
    statusOptions: [
      { label: 'All rooms', value: '' },
      { label: 'Incomplete', value: 'incomplete' },
      { label: 'Completed', value: 'completed' },
      { label: 'Locked', value: 'locked' },
      { label: 'Unlocked', value: 'unlocked' }
    ]
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    blockOptions () {
      return [{ label: 'Any block', value: null }].concat(
        this.blocks.map((block) => ({ label: block.name, value: block.id })))
    },
    locationOptions () {
      return [{ label: 'Any location', value: null }].concat(
        this.locations.map((location) => ({ label: location.name, value: location.id })))
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
      this.locations = await get('/api/event/' + this.event.id + '/hotel_location', { sort: 'name' })
      if (this.$route.query.block) {
        this.block = parseInt(this.$route.query.block) || null
      }
      await this.loadRooms()
    },
    async loadRooms () {
      if (!this.event) {
        return
      }
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
      if (this.status) {
        params.status = this.status
      }
      if (this.location) {
        params.hotel_location = this.location
      }
      const found = await get('/api/event/' + this.event.id + '/hotel/room_search', params)
      this.rooms = found.hotel_rooms || []
      this.count = found.count || 0
      const ids = this.rooms.map((x) => x.id)
      this.roomDetails = ids.length
        ? await get('/api/event/' + this.event.id + '/hotel/room_details', { rooms: ids.join(',') })
        : {}
      this.loading = false
    },
    occupants (room) {
      const details = this.roomDetails[room.id]
      return details ? Object.values(details.roommates) : []
    },
    issues (room) {
      return this.occupants(room).flatMap(
        (mate) => mate.errors.map((error) => mate.name + ': ' + error))
    },
    formatTimestamp (value) {
      if (!value) {
        return ''
      }
      const d = new Date(value)
      return isNaN(d.getTime()) ? '' : d.toLocaleString()
    },
    async setBlock (room, blockId) {
      await patch('/api/event/' + this.event.id + '/hotel_room/' + room.id,
        { id: room.id, hotel_block: blockId })
      room.hotel_block = blockId
      this.$toast.add({ severity: 'success', summary: 'Block Updated', life: 1500 })
    },
    async exportPasskey () {
      try {
        await download('/api/event/' + this.event.id + '/hotel/export_passkey',
          'passkey_rooms.csv')
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Export Failed', life: 3000 })
      }
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
      this.offset = 0
      this.loadRooms()
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
      if (JSON.stringify(query) !== JSON.stringify(this.$route.query)) {
        this.$router.replace({ query })
      }
      this.onFilter()
    },
    status () {
      this.onFilter()
    },
    location () {
      this.onFilter()
    }
  }
}
</script>
