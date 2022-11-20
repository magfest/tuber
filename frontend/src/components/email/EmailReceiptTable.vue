<template>
  <div>
    <tuber-table tableTitle="Email Receipts" formTitle="Email Receipt" url="/api/event/<event>/email_receipt"
      :parameters="parameters" :filters="filters">

      <template #controls>
        <div></div>
      </template>

      <template #columns>
        <Column field="subject" filterField="subject" header="Subject" :sortable="true">
          <template #filter="{ filterModel, filterCallback }">
            <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"
              :placeholder="`Search by Subject`" v-tooltip.top.focus="'Hit enter key to filter'" />
          </template>
        </Column>
        <Column field="to_address" filterField="to_address" header="To" :sortable="true">
          <template #filter="{ filterModel, filterCallback }">
            <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"
              :placeholder="`Search by Address`" v-tooltip.top.focus="'Hit enter key to filter'" />
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
        <email-receipt-form :modelValue="props.modelValue" />
      </template>

      <template #formActions="props">
        <Button label="Close" @click="props.cancel"></Button>
      </template>
    </tuber-table>
  </div>
</template>

<script>
import EmailReceiptForm from './EmailReceiptForm.vue'
import TuberTable from '../TuberTable.vue'
import { FilterMatchMode } from 'primevue/api'

export default {
  name: 'EmailReceiptTable',
  components: {
    TuberTable,
    EmailReceiptForm
  },
  data: () => ({
    filters: {
      subject: { value: null, matchMode: FilterMatchMode.CONTAINS },
      to_address: { value: null, matchMode: FilterMatchMode.CONTAINS },
      timestamp: { value: null, matchMode: FilterMatchMode.GREATER_THAN_OR_EQUAL_TO }
    },
    parameters: {
      full: true
    }
  })
}
</script>
