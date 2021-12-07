<template>
    <div>
      <tuber-table tableTitle="Hotel Room Requests" formTitle="Hotel Room Request" url="/api/event/<event>/hotel_room_request"
        :parameters="parameters" :format="format" :autoload="false" ref="table" :filters="filters">

        <template #controls>
          <Dropdown :options="hotelBlocks" optionLabel="name" optionValue="id" v-model="hotelBlock" />
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
              <Tag v-for="night in roomNights" :key="slotProps.data.id + '_' + night.id" :value="night.name.slice(0,2)" :severity="slotProps.data.nights[night.id] ? 'primary': (slotProps.data.nights_requested[night.id] ? 'warning' : 'danger')" class="mr-1" style="width: 27px" />
            </template>
          </Column>
          <Column field="notes" filterField="notes" header="Notes" :sortable="true"></Column>
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
import { get, patch } from '@/lib/rest'
import RequestShortForm from './RequestShortForm.vue'
import TuberTable from '../../TuberTable.vue'
import { FilterMatchMode } from 'primevue/api'
import { ModelActionTypes } from '@/store/modules/models/actions'

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
    }
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    parameters () {
      const params = {
        full: true,
        deep: true
      }
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
    async load () {
      this.$store.dispatch(ModelActionTypes.LOAD_BADGES)
      this.roomNights = await get('/api/event/' + this.event.id + '/hotel_room_night')
      this.hotelBlocks = await get('/api/event/' + this.event.id + '/hotel_room_block')
      if (this.hotelBlocks && !this.hotelBlocks.includes(this.hotelBlock)) {
        this.hotelBlock = this.hotelBlocks[0].id
      }
    },
    async save (props) {
      try {
        const request = {}
        Object.assign(request, props.edited)
        request.requested_roommates = []
        for (const roommate of request.roommate_requests) {
          request.requested_roommates.push(roommate.id)
        }
        request.antirequested_roommates = []
        for (const roommate of request.roommate_anti_requests) {
          request.antirequested_roommates.push(roommate.id)
        }
        await patch('/api/event/' + this.event.id + '/hotel/request/' + request.id, request)
        props.cancel()
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', detail: 'Your request has been saved. You may continue editing it until the deadline.', life: 3000 })
      } catch (error) {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 3000 })
      }
    },
    async format (requests) {
      const filtered = []
      for (const req of requests) {
        const item = {}
        Object.assign(item, req)
        item.room_nights = []
        item.nights = {}
        item.nights_requested = {}
        for (const rn of this.roomNights) {
          const night = {
            name: rn.name,
            id: rn.id
          }
          let requested = false
          for (const nightreq of item.room_night_requests) {
            if (nightreq.room_night === rn.id && nightreq.requested) {
              requested = true
              break
            }
          }
          if (rn.restricted) {
            night.approved = false
            for (const nightapp of item.room_night_approvals) {
              if (nightapp.room_night === rn.id && nightapp.approved) {
                night.approved = true
                break
              }
            }
          } else {
            night.approved = requested
          }
          night.requested = requested
          item.nights[rn.id] = night.approved
          item.nights_requested[rn.id] = night.requested
          item.room_nights.push(night)
        }
        filtered.push(item)
      }
      return filtered
    }
  },
  watch: {
    event () {
      this.load()
    }
  }
}
</script>
