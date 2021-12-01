<template>
    <div>
      <tuber-table formTitle="Email Source" url="/api/event/<event>/email_source"
        :filters="filters">

        <template #columns>
          <Column field="name" filterField="name" header="Name" :sortable="true" />
          <Column field="description" filterField="description" header="Description" :sortable="true" />
          <Column field="address" filterField="address" header="Address" :sortable="true" />
          <Column field="region" filterField="region" header="Region" :sortable="true" />
          <Column field="active" filterField="active" header="Active" :sortable="true" />
        </template>

        <template #form="props">
          <email-source-form :modelValue="props.modelValue" />
        </template>
      </tuber-table>
    </div>
</template>

<script>
import EmailSourceForm from './EmailSourceForm.vue'
import TuberTable from '../TuberTable.vue'
import { FilterMatchMode } from 'primevue/api'

export default {
  name: 'EmailSourceTable',
  components: {
    TuberTable,
    EmailSourceForm
  },
  data: () => ({
    filters: {
      name: { value: null, matchMode: FilterMatchMode.CONTAINS },
      description: { value: null, matchMode: FilterMatchMode.CONTAINS },
      address: { value: null, matchMode: FilterMatchMode.CONTAINS },
      region: { value: null, matchMode: FilterMatchMode.CONTAINS },
      active: { value: null, matchMode: FilterMatchMode.CONTAINS }
    }
  })
}
</script>
