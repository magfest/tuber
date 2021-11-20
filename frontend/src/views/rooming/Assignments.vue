<template>
  <div class="card">
    <Toast />
    <h3>Room Assignments</h3>
    <Toolbar class="mb-1">
        <template #left>
            <Button class="p-button-success mr-2"><u>C</u>reate Room</Button>
            <Button class="p-button-info mr-2"><u>R</u>ematch All</Button>
            <Dropdown :options="blocks" v-model="block" />
        </template>

        <template #right>
            <span class="p-input-icon-left">
                <i class="pi pi-search" />
                <InputText type="text" placeholder="Search" />
            </span>
        </template>
    </Toolbar>
    <div class="grid">
      <div class="col">
        <DataTable class="p-datatable-sm" sortField="public_name" :sortOrder="1" selectionMode="multiple" :value="formattedRequests" :paginator="true" :rows="25" dataKey="id" v-model:filters="requestFilters" filterDisplay="row"
          :loading="loading" :globalFilterFields="['public_name']" v-model:selection="selectedRequests">
          <Column header="Name" field="public_name" filterField="public_name" style="width: 8rem" :sortable="true">
          </Column>
          <Column header="Nights" field="room_nights" filterField="room_nights" style="width: 13rem" :sortable="true">
            <template #body="slotProps">
              <Tag v-for="night in slotProps.data.room_nights" :key="night.id" :value="night.name.slice(0,2)" :severity="night.assigned ? 'primary': 'danger'" class="mr-1" />
            </template>
          </Column>
          <Column header="Notes" field="notes" filterField="notes">
          </Column>
        </DataTable>
      </div>
      <div class="col">
        <div class="field-checkbox">
          <Checkbox id="hidecomplete" v-model="hidecompleted" :binary="true" />
          <label for="hidecomplete">Hide Completed</label>
        </div>
        <Card v-for="room in filteredRooms" :key="room.id" class="mb-2">
            <template #title>
              <div class="flex justify-content-between">
                <InputText v-if="room.edit" v-model="room.name" @blur="room.edit=false" />
                <span v-else @click="room.edit=true">
                  {{ room.name ? room.name : "Room " + room.id}}
                </span>
                <span>
                  <Button v-if="room.completed" class="p-button-info mr-2" icon="pi pi-check" @click="room.completed=false" />
                  <Button v-else class="p-button-success mr-2" icon="pi pi-check" @click="room.completed=true" />
                  <Button class="p-button-danger">Remove</Button>
                </span>
              </div>
            </template>
            <template #content>
              <div class="grid">
                <div class="col">
                  <div><Button class="p-button-danger minibutton" icon="pi pi-times" iconPos="right" />Mark Murnane</div>
                  <div><Button class="p-button-danger minibutton" icon="pi pi-times" iconPos="right" />Mark Murnane</div>
                  <div><Button class="p-button-danger minibutton" icon="pi pi-times" iconPos="right" />Mark Murnane</div>
                  <div><Button class="p-button-danger minibutton" icon="pi pi-times" iconPos="right" />Mark Murnane</div>
                  <div><Button class="p-button-success minibutton" icon="pi pi-plus" iconPos="rigth" /></div>
                </div>
                <div class="col">
                  <Textarea v-model="room.notes" rows="5" />
                </div>
              </div>
            </template>
        </Card>
      </div>
    </div>
  </div>
</template>

<style>
.p-card .p-card-content {
  padding-top: 0;
  padding-bottom: 0;
}
.p-button.p-button-icon-only.minibutton {
  padding-top: 0;
  padding-bottom: 0;
  width: 19px;
  margin-bottom: 2px;
  margin-right: 2px;
}
</style>

<script>
import { mapGetters } from 'vuex'
import { get } from '@/lib/rest'
import { FilterMatchMode } from 'primevue/api'
import { ModelActionTypes } from '@/store/modules/models/actions'

export default {
  name: 'RoomAssignments',
  props: [
    ''
  ],
  components: {
  },
  data: () => ({
    blocks: [
      'General Staff',
      'Consoles'
    ],
    block: '',
    loading: false,
    hidecompleted: true,
    requests: [],
    rooms: [],
    requestFilters: {
      global: { value: null, matchMode: FilterMatchMode.CONTAINS },
      public_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
      nights: { value: null, matchMode: FilterMatchMode.EQUALS }
    },
    roomFilters: {
      global: { value: null, matchMode: FilterMatchMode.CONTAINS },
      name: { value: null, matchMode: FilterMatchMode.CONTAINS }
    },
    selectedRequests: [],
    selectedRooms: []
  }),
  computed: {
    ...mapGetters([
      'event',
      'badgeLookup'
    ]),
    formattedRequests () {
      const formatted = []
      for (const req of this.requests) {
        if (Object.prototype.hasOwnProperty.call(this.badgeLookup, req.badge)) {
          let publicName = this.badgeLookup[req.badge].public_name
          if (!publicName) {
            publicName = this.badgeLookup[req.badge].first_name + ' ' + this.badgeLookup[req.badge].last_name
          }
          formatted.push({
            id: req.id,
            public_name: publicName,
            room_nights: [
              { id: 1, name: 'Tuesday', assigned: true },
              { id: 2, name: 'Wednesday', assigned: false },
              { id: 3, name: 'Thursday', assigned: true },
              { id: 4, name: 'Friday', assigned: true },
              { id: 5, name: 'Saturday', assigned: true },
              { id: 6, name: 'Sunday', assigned: false }
            ],
            notes: req.notes
          })
        }
      }
      return formatted
    },
    filteredRooms () {
      const filtered = []
      for (const room of this.rooms) {
        if (this.hidecompleted) {
          if (!room.completed) {
            filtered.push(room)
          }
        } else {
          filtered.push(room)
        }
      }
      return filtered.slice(0, 10)
    }
  },
  mounted () {
    this.load()
  },
  methods: {
    async load () {
      this.loading = true
      await this.$store.dispatch(ModelActionTypes.LOAD_BADGES)
      try {
        this.requests = await get('/api/event/' + this.event.id + '/hotel_room_request')
        this.rooms = await get('/api/event/' + this.event.id + '/hotel_room')
      } catch (error) {

      }
      this.loading = false
    }
  },
  watch: {
    event () {
      this.load()
    }
  }
}
</script>
