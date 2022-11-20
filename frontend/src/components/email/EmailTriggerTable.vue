<template>
  <div>
    <tuber-table tableTitle="Email Triggers" formTitle="Email Trigger" url="/api/event/<event>/email_trigger"
      :parameters="parameters" :filters="filters">

      <template #controls>
        <div></div>
      </template>

      <template #columns>
        <Column field="trigger" filterField="trigger" header="Trigger" :sortable="true">
          <template #filter="{ filterModel, filterCallback }">
            <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"
              :placeholder="`Search by Trigger`" v-tooltip.top.focus="'Hit enter key to filter'" />
          </template>
        </Column>
        <Column field="timestamp" filterField="timestamp" header="Timestamp" :sortable="true">
          <template #filter="{ filterModel, filterCallback }">
            <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"
              :placeholder="`Search by Timestamp`" v-tooltip.top.focus="'Hit enter key to filter'" />
          </template>
        </Column>
      </template>

      <template #actions="props">
        <Column header="Actions" style="width: 10rem">
          <template #body="slotProps">
            <Button @click="props.edit(slotProps.data)" icon="pi pi-eye" class="p-button-info" />
          </template>
        </Column>
      </template>

      <template #form="props">
        <email-trigger-form :modelValue="props.modelValue" />
      </template>

      <template #formActions="props">
        <Button label="Close" @click="props.cancel"></Button>
      </template>
    </tuber-table>
  </div>
</template>

<script>
import EmailTriggerForm from './EmailTriggerForm.vue'
import TuberTable from '../TuberTable.vue'
import { FilterMatchMode } from 'primevue/api'

export default {
  name: 'EmailTriggerTable',
  components: {
    TuberTable,
    EmailTriggerForm
  },
  data: () => ({
    filters: {
      trigger: { value: null, matchMode: FilterMatchMode.CONTAINS },
      timestamp: { value: null, matchMode: FilterMatchMode.GREATER_THAN_OR_EQUAL_TO }
    },
    parameters: {
      full: true
    }
  })
}
</script>
