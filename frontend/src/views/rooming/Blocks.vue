<template>
  <div class="card">
    <Toast />
    <h3>Room Blocking</h3>
    <Dropdown v-model="selectedRoomBlock" :options="room_blocks" optionLabel="name" optionValue="id" placeholder="Any" class="p-column-filter" ref="room_block"></Dropdown><Button @click="saveSelected" :disabled="selected.length === 0">Apply Selected</Button>
    <DataTable :value="requests" :paginator="true" :rows="25" dataKey="id" v-model:filters="filters" filterDisplay="row" :loading="loading"
                :globalFilterFields="['name','departments','badge_type']" v-model:selection="selected">
        <Column selectionMode="multiple" style="width: 3rem"></Column>
        <Column header="Name" field="public_name" filterField="public_name" :sortable="true">
            <template #filter="{filterModel,filterCallback}">
                <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" :placeholder="`Search by name - `" v-tooltip.top.focus="'Hit enter key to filter'"/>
            </template>
        </Column>
        <Column header="Departments" filterField="departments">
            <template #body="slotProps">
                {{ slotProps.data.department_names.join(", ") }}
            </template>
            <template #filter="{filterModel,filterCallback}">
                <Dropdown v-model="filterModel.value" @change="filterCallback()" :options="departments" optionLabel="name" optionValue="id" placeholder="Any" class="p-column-filter"></Dropdown>
            </template>
        </Column>
        <Column header="Badge Type" filterField="badge_type" :sortable="true">
            <template #body="slotProps">
                {{ badgeTypeLookup[slotProps.data.badge_type].name }}
            </template>
            <template #filter="{filterModel,filterCallback}">
                <Dropdown v-model="filterModel.value" @change="filterCallback()" :options="badgeTypes" optionLabel="name" optionValue="id" placeholder="Any" class="p-column-filter"></Dropdown>
            </template>
        </Column>
        <Column header="Room Block" filterField="room_block" :sortable="true">
            <template #body="slotProps">
                <Dropdown v-model="slotProps.data.hotel_block" @change="save(slotProps.data.hotel_room_request, slotProps.data.room_block)" :options="room_blocks" optionLabel="name" optionValue="id"></Dropdown>
            </template>
            <template #filter="{filterModel,filterCallback}">
                <Dropdown v-model="filterModel.value" @change="filterCallback()" :options="room_blocks" optionLabel="name" optionValue="id" placeholder="Any" class="p-column-filter"></Dropdown>
            </template>
        </Column>
    </DataTable>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex'
import { get, post, patch } from '@/lib/rest'
import { ModelActionTypes } from '@/store/modules/models/actions'
import { FilterMatchMode } from 'primevue/api'

export default {
  name: 'RoomBlocks',
  props: [
    ''
  ],
  components: {
  },
  data: () => ({
    requests: [],
    filters: {
      global: { value: null, matchMode: FilterMatchMode.CONTAINS },
      public_name: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
      departments: { value: null, matchMode: FilterMatchMode.CONTAINS },
      badge_type: { value: null, matchMode: FilterMatchMode.EQUALS },
      room_block: { value: null, matchMode: FilterMatchMode.EQUALS }
    },
    loading: false,
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
    this.load()
  },
  methods: {
    async load () {
      this.loading = true
      await this.$store.dispatch(ModelActionTypes.LOAD_BADGETYPES)
      await this.$store.dispatch(ModelActionTypes.LOAD_DEPARTMENTS)
      await this.$store.dispatch(ModelActionTypes.LOAD_BADGETYPES)
      this.room_blocks = await get('/api/event/' + this.event.id + '/hotel_room_block')
      this.requests = await get('/api/event/' + this.event.id + '/hotel/block_assignments')
      this.loading = false
    },
    save (hotelRoomRequest, roomBlock) {
      patch('/api/event/' + this.event.id + '/hotel_room_request/' + hotelRoomRequest, { hotel_block: roomBlock }).then(() => {
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 300 })
      }).catch(() => {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 300 })
      })
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
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 300 })
      }).catch(() => {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 300 })
      })
    }
  },
  watch: {
    event () {
      this.load()
    }
  }
}
</script>
