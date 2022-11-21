<template>
  <div class="card">
    <Toast />
    <tuber-table tableTitle="Room Blocking" formTitle="" url="/api/event/<event>/hotel/block_assignments" :filters="filters" :showActions="false" :onSelect="onSelect">
      <template #controls>
        <div>
          <Dropdown v-model="selectedRoomBlock" :options="room_blocks" optionLabel="name" optionValue="id" placeholder="Any" class="p-column-filter" ref="room_block"></Dropdown>
          <Button @click="saveSelected" :disabled="selected.length === 0">Apply Selected</Button>
        </div>
      </template>

      <template #columns>
        <Column selectionMode="multiple" style="width: 3rem"></Column>

        <Column header="Name" field="public_name" filterField="public_name" :sortable="true">
            <template #filter="{filterModel,filterCallback}">
                <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" :placeholder="`Search by name - `" v-tooltip.top.focus="'Hit enter key to filter'"/>
            </template>
        </Column>

        <Column field="departments" header="Departments" filterField="departments">
            <template #body="slotProps">
                {{ slotProps.data.department_names.join(', ') }}
            </template>
            <template #filter="{filterModel,filterCallback}">
                <Dropdown v-model="filterModel.value" @change="filterCallback()" :options="departments" optionLabel="name" optionValue="id" placeholder="Any" class="p-column-filter"></Dropdown>
            </template>
        </Column>

        <Column header="Notes" field="notes" :sortable="true">
          <template #filter="{filterModel,filterCallback}">
                <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" :placeholder="`Search by notes - `" v-tooltip.top.focus="'Hit enter key to filter'"/>
            </template>
        </Column>

        <Column header="Room Block" filterField="hotel_block" :sortable="true" style="width: 12rem">
            <template #body="slotProps">
                <Dropdown v-model="slotProps.data.hotel_block" @change="save(slotProps.data.hotel_room_request, slotProps.data.hotel_block)" :options="room_blocks" optionLabel="name" optionValue="id"></Dropdown>
            </template>
            <template #filter="{filterModel,filterCallback}">
                <Dropdown v-model="filterModel.value" @change="filterCallback()" :options="room_blocks" optionLabel="name" optionValue="id" placeholder="Any" class="p-column-filter"></Dropdown>
            </template>
        </Column>
      </template>
    </tuber-table>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex'
import { get, post, patch } from '@/lib/rest'
import { ModelActionTypes } from '@/store/modules/models/actions'
import { FilterMatchMode } from 'primevue/api'
import TuberTable from '../../components/TuberTable.vue'

export default {
  name: 'RoomBlocks',
  props: [
    ''
  ],
  components: {
    TuberTable
  },
  data: () => ({
    filters: {
      public_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
      departments: { value: null, matchMode: FilterMatchMode.CONTAINS },
      notes: { value: null, matchMode: FilterMatchMode.CONTAINS },
      hotel_block: { value: null, matchMode: FilterMatchMode.EQUALS }
    },
    selected: [],
    selectedRoomBlock: null,
    room_blocks: []
  }),
  computed: {
    ...mapGetters([
      'event',
      'departmentLookup',
      'departments',
      'badgeTypeLookup',
      'badgeTypes'
    ])
  },
  mounted () {
    if (this.event) {
      this.load()
    }
  },
  methods: {
    async load () {
      this.loading = true
      await this.$store.dispatch(ModelActionTypes.LOAD_DEPARTMENTS)
      await this.$store.dispatch(ModelActionTypes.LOAD_BADGETYPES)
      const roomblocks = await get('/api/event/' + this.event.id + '/hotel_room_block', { sort: 'name' })
      roomblocks.push({
        description: 'No Block Assigned',
        event: this.event.id,
        id: -1,
        name: '---'
      })
      this.room_blocks = roomblocks
      this.loading = false
    },
    async save (hotelRoomRequest, roomBlock) {
      try {
        if (roomBlock === -1) {
          await patch('/api/event/' + this.event.id + '/hotel_room_request/' + hotelRoomRequest, { hotel_block: null })
        } else {
          await patch('/api/event/' + this.event.id + '/hotel_room_request/' + hotelRoomRequest, { hotel_block: roomBlock })
        }
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 1000 })
      } catch {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 3000 })
      }
    },
    saveSelected () {
      const updates = []
      for (const entry of this.selected) {
        updates.push({
          id: entry.hotel_room_request,
          hotel_block: this.selectedRoomBlock
        })
        entry.hotel_block = this.selectedRoomBlock
      }

      post('/api/event/' + this.event.id + '/hotel/block_assignments', { updates: updates }).then(() => {
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 1000 })
      }).catch(() => {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 3000 })
      })
    },
    onSelect (data) {
      this.selected = data
    }
  },
  watch: {
    event () {
      this.load()
    }
  }
}
</script>
