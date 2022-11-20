<template>
    <div>
        <tuber-table tableTitle="Events" formTitle="Event" url="/api/event" :filters="filters">

            <template #columns>
                <Column field="name" filterField="name" header="Name" :sortable="true">
                    <template #filter="{ filterModel, filterCallback }">
                        <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()"
                            class="p-column-filter" :placeholder="`Search by Name`"
                            v-tooltip.top.focus="'Hit enter key to filter'" />
                    </template>
                </Column>
                <Column field="description" filterField="description" header="Description" :sortable="true">
                    <template #filter="{ filterModel, filterCallback }">
                        <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()"
                            class="p-column-filter" :placeholder="`Search by Description`"
                            v-tooltip.top.focus="'Hit enter key to filter'" />
                    </template>
                </Column>
                <Column field="readonly" header="Read-Only" style="width: 8rem">
                    <template #body="slotProps">
                        <i class="pi pi-check" v-if="slotProps.data.readonly" />
                        <i class="pi pi-times" v-else />
                    </template>
                    <template #filter="{ filterModel, filterCallback }">
                        <TriStateCheckbox v-model="filterModel.value" @change="filterCallback()"
                            class="p-column-filter" />
                    </template>
                </Column>
            </template>

            <template #actions="tableProps">
                <Column header="Actions" style="width: 15rem">
                    <template #body="slotProps">
                        <Button @click="tableProps.edit(slotProps.data)" icon="pi pi-cog" class="p-button-info ml-2" />
                        <Button @click="tableProps.remove($event, slotProps.data)" icon="pi pi-times"
                            class="p-button-danger ml-2" />
                    </template>
                </Column>
            </template>

            <template #form="props">
                <event-form :modelValue="props.modelValue" />
            </template>
        </tuber-table>
    </div>
</template>

<script>
import EventForm from './EventForm.vue'
import TuberTable from '../TuberTable.vue'
import { FilterMatchMode } from 'primevue/api'

export default {
  name: 'EventTable',
  components: {
    TuberTable,
    EventForm
  },
  data: () => ({
    filters: {
      name: { value: null, matchMode: FilterMatchMode.CONTAINS },
      description: { value: null, matchMode: FilterMatchMode.CONTAINS },
      readonly: { value: null, matchMode: FilterMatchMode.EQUALS }
    }
  })
}
</script>
