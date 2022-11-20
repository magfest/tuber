<template>
  <div>
    <tuber-table tableTitle="Email Sources" formTitle="Email Source" url="/api/event/<event>/email_source"
      :filters="filters">

      <template #columns>
        <Column field="name" filterField="name" header="Name" :sortable="true">
          <template #filter="{ filterModel, filterCallback }">
            <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"
              :placeholder="`Search by Name`" v-tooltip.top.focus="'Hit enter key to filter'" />
          </template>
        </Column>
        <Column field="description" filterField="description" header="Description" :sortable="true">
          <template #filter="{ filterModel, filterCallback }">
            <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"
              :placeholder="`Search by Description`" v-tooltip.top.focus="'Hit enter key to filter'" />
          </template>
        </Column>
        <Column field="address" filterField="address" header="Address" :sortable="true">
          <template #filter="{ filterModel, filterCallback }">
            <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"
              :placeholder="`Search by Address`" v-tooltip.top.focus="'Hit enter key to filter'" />
          </template>
        </Column>
        <Column field="region" filterField="region" header="Region" :sortable="true">
          <template #filter="{ filterModel, filterCallback }">
            <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"
              :placeholder="`Search by Region`" v-tooltip.top.focus="'Hit enter key to filter'" />
          </template>
        </Column>
        <Column field="active" header="Active" :sortable="true" style="width: 8rem">
          <template #body="slotProps">
            <i class="pi pi-check" v-if="slotProps.data.active" />
            <i class="pi pi-times" v-else />
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <TriStateCheckbox v-model="filterModel.value" @change="filterCallback()" class="p-column-filter" />
          </template>
        </Column>
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
      active: { value: null, matchMode: FilterMatchMode.EQUALS }
    }
  })
}
</script>
