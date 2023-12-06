<template>
  <div>
    <a ref="download" />
    <tuber-table tableTitle="Emails" formTitle="Email" url="/api/event/<event>/email" :parameters="parameters"
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
        <Column field="subject" filterField="subject" header="Subject" :sortable="true">
          <template #filter="{ filterModel, filterCallback }">
            <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"
              :placeholder="`Search by Address`" v-tooltip.top.focus="'Hit enter key to filter'" />
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
        <Column field="send_once" header="Send Once" :sortable="true" style="width: 8rem">
          <template #body="slotProps">
            <i class="pi pi-check" v-if="slotProps.data.send_once" />
            <i class="pi pi-times" v-else />
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <TriStateCheckbox v-model="filterModel.value" @change="filterCallback()" class="p-column-filter" />
          </template>
        </Column>
      </template>

      <template #actions="tableProps">
        <Column header="Actions" style="width: 15rem">
          <template #body="slotProps">
            <Button @click="trigger(slotProps.data)" icon="pi pi-send" class="p-button-info ml-2" />
            <Button @click="csv(slotProps.data)" icon="pi pi-download" class="p-button-info ml-2" />
            <Button @click="tableProps.edit(slotProps.data)" icon="pi pi-cog" class="p-button-info ml-2" />
            <Button @click="tableProps.remove($event, slotProps.data)" icon="pi pi-times"
              class="p-button-danger ml-2" />
          </template>
        </Column>
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
import { mapGetters } from 'vuex'
import { post } from '../../lib/rest'
import { VueCookieNext } from 'vue-cookie-next'

export default {
  name: 'EmailTable',
  components: {
    TuberTable,
    EmailForm
  },
  data: () => ({
    filters: {
      name: { value: null, matchMode: FilterMatchMode.CONTAINS },
      description: { value: null, matchMode: FilterMatchMode.CONTAINS },
      subject: { value: null, matchMode: FilterMatchMode.CONTAINS },
      active: { value: null, matchMode: FilterMatchMode.EQUALS },
      send_once: { value: null, matchMode: FilterMatchMode.EQUALS }
    },
    parameters: {
      full: true
    }
  }),
  computed: {
    ...mapGetters([
      'event'
    ])
  },
  methods: {
    async csv (email) {
      const headers = {
        Accept: 'text/csv',
        'CSRF-Token': VueCookieNext.getCookie('csrf_token')
      }

      const response = await fetch('/api/event/' + this.event.id + '/email/' + email.id + '/csv', {
        method: 'GET',
        headers,
        body: null,
        credentials: 'include'
      })

      if (response.status === 200) {
        const body = await response.blob()
        const text = await body.text()
        this.$refs.download.setAttribute('href', 'data:text/csv;charset=utf-8, ' + encodeURIComponent(text))
        this.$refs.download.setAttribute('download', 'emails.csv')
        this.$refs.download.click()
      }
    },
    async trigger (email) {
      await post('/api/event/' + this.event.id + '/email/' + email.id + '/trigger')
    }
  }
}
</script>
