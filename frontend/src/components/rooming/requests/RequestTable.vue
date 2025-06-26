<template>
    <div>
      <tuber-table tableTitle="Hotel Room Requests" formTitle="Hotel Room Request" url="/api/event/<event>/hotel/list_requests"
        :parameters="parameters" :autoload="false" ref="table" :filters="filters">

        <template #controls>
          <Dropdown :options="hotelBlocks" optionLabel="name" optionValue="id" v-model="hotelBlock" showClear />
        </template>

        <template #columns>
          <Column field="first_name" filterField="first_name" header="First Name" :sortable="true">
            <template #filter="{filterModel,filterCallback}">
                <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" :placeholder="`Search Requests by Name`" v-tooltip.top.focus="'Hit enter key to filter'"/>
            </template>
          </Column>
          <Column field="last_name" filterField="last_name" header="Last Name" :sortable="true">
            <template #filter="{filterModel,filterCallback}">
                <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" :placeholder="`Search Requests by Name`" v-tooltip.top.focus="'Hit enter key to filter'"/>
            </template>
          </Column>
          <Column header="Room Nights">
            <template #body="slotProps">
              <Tag v-for="night in roomNights" :key="slotProps.data.id + '_' + night.id" :value="night.name.slice(0,2)" :severity="slotProps.data.approved_nights[night.id] ? 'primary': (slotProps.data.requested_nights[night.id] ? 'warning' : 'danger')" class="mr-1" style="width: 18px" />
            </template>
          </Column>
          <Column field="notes" filterField="notes" header="Notes" :sortable="true"></Column>
        </template>

        <template #actions="props">
          <Column header="Actions" style="width: 10rem">
            <template #body="slotProps">
              <Button @click="loadmodel(props.edit, slotProps.data)" icon="pi pi-cog" class="p-button-info" />
              <Button @click="props.remove($event, slotProps.data)" icon="pi pi-times" class="p-button-danger ml-2" />
            </template>
          </Column>
        </template>

        <template #form="props">
          <request-short-form :modelValue="props.modelValue" />
        </template>

        <template #formActions="props">
          <Button label="Cancel" @click="props.cancel" icon="pi pi-times" class="p-button-text"/>
          <Button label="Save" @click="save(props)" icon="pi pi-check" autofocus />
        </template>
      </tuber-table>
    </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { get, patch } from '../../../lib/rest'
import RequestShortForm from './RequestShortForm.vue'
import TuberTable from '../../TuberTable.vue'
import { FilterMatchMode } from 'primevue/api'

export default {
  name: 'RequestTable',
  components: {
    TuberTable,
    RequestShortForm
  },
  data: () => ({
    hotelBlocks: [],
    hotelBlock: null,
    roomNights: [],
    filters: {
      first_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
      last_name: { value: null, matchMode: FilterMatchMode.CONTAINS }
    },
    editedID: null,
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    parameters () {
      const params = {}
      if (this.hotelBlock) {
        params.hotel_block = this.hotelBlock
      }
      return params
    }
  },
  mounted () {
    if (this.event) {
      this.load()
    }
  },
  methods: {
    async loadmodel (edit, model) {
      this.editedID = model.id
      const editmodel = await get('/api/event/' + this.event.id + '/hotel/request/' + model.id);
      edit(editmodel)
    },
    async load () {
      this.roomNights = await get('/api/event/' + this.event.id + '/hotel_room_night', { sort: 'date' })
      this.hotelBlocks = await get('/api/event/' + this.event.id + '/hotel_room_block', { sort: 'name' })
      if (this.hotelBlocks && !this.hotelBlocks.includes(this.hotelBlock)) {
        this.hotelBlock = this.hotelBlocks[0].id
      }
    },
    async save (props) {
      try {
        await patch('/api/event/' + this.event.id + '/hotel/request/' + this.editedID, props.edited)
        props.cancel()
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', detail: 'Your request has been saved. You may continue editing it until the deadline.', life: 3000 })
      } catch (error) {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 3000 })
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
