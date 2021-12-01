<template>
    <div>
      <tuber-table formTitle="Email" url="/api/event/<event>/email"
        :parameters="parameters" :filters="filters">

        <template #columns>
          <Column field="name" filterField="name" header="Name" :sortable="true" />
          <Column field="description" filterField="description" header="Description" :sortable="true" />
          <Column field="subject" filterField="subject" header="Subject" :sortable="true" />
          <Column field="active" filterField="active" header="Active" :sortable="true" />
          <Column field="send_once" filterField="send_once" header="Send Once" :sortable="true" />
        </template>

        <template #form="props">
          <email-form :modelValue="props.modelValue" />
        </template>
      </tuber-table>
    </div>
</template>

<script>
import EmailForm from './EmailForm.vue'
import TuberTable from '../TuberTable.vue'
import { FilterMatchMode } from 'primevue/api'

export default {
  name: 'EmailTriggerTable',
  components: {
    TuberTable,
    EmailForm
  },
  data: () => ({
    filters: {
      name: { value: null, matchMode: FilterMatchMode.CONTAINS },
      description: { value: null, matchMode: FilterMatchMode.CONTAINS },
      subject: { value: null, matchMode: FilterMatchMode.CONTAINS },
      active: { value: null, matchMode: FilterMatchMode.CONTAINS },
      send_once: { value: null, matchMode: FilterMatchMode.CONTAINS }
    },
    parameters: {
      full: true
    }
  })
}
</script>
