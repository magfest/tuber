<template>
    <div>
      <a ref="download" />
      <tuber-table formTitle="Email" url="/api/event/<event>/email"
        :parameters="parameters" :filters="filters">

        <template #columns>
          <Column field="name" filterField="name" header="Name" :sortable="true" />
          <Column field="description" filterField="description" header="Description" :sortable="true" />
          <Column field="subject" filterField="subject" header="Subject" :sortable="true" />
          <Column field="active" filterField="active" header="Active" :sortable="true" />
          <Column field="send_once" filterField="send_once" header="Send Once" :sortable="true" />
        </template>

        <template #actions="tableProps">
          <Column header="Actions" style="width: 15rem">
            <template #body="slotProps">
                <Button @click="trigger(slotProps.data)" icon="pi pi-send" class="p-button-info ml-2" />
                <Button @click="csv(slotProps.data)" icon="pi pi-download" class="p-button-info ml-2" />
                <Button @click="tableProps.edit(slotProps.data)" icon="pi pi-cog" class="p-button-info ml-2" />
                <Button @click="tableProps.remove($event, slotProps.data)" icon="pi pi-times" class="p-button-danger ml-2" />
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
import { post } from '@/lib/rest'
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
      active: { value: null, matchMode: FilterMatchMode.CONTAINS },
      send_once: { value: null, matchMode: FilterMatchMode.CONTAINS }
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
