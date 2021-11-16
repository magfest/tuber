<template>
    <div>
    <DataTable :value="hotelRequests" :loading="loading" :paginator="true" :rows="25">
        <Column field="public_name" header="Name" :sortable="true"></Column>
        <Column field="notes" header="Notes" :sortable="true"></Column>
        <Column header="Actions" style="width: 5rem">
            <template #body="slotProps">
                <Button @click="edit(slotProps.data)" icon="pi pi-cog" class="p-button-rounded" />
            </template>
        </Column>
        </DataTable>

        <Dialog v-model:visible="editing">
            <template #header>
                <h3>Hotel Room Night</h3>
            </template>

            <request-form :id="edited" ref="form" />

            <template #footer>
                <Button label="Cancel" @click="cancel" icon="pi pi-times" class="p-button-text"/>
                <Button label="Save" @click="save" icon="pi pi-check" autofocus />
            </template>
        </Dialog>
    </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { get } from '@/lib/rest'
import RequestForm from './RequestForm.vue'

export default {
  name: 'RequestTable',
  props: [
  ],
  components: {
    RequestForm
  },
  data: () => ({
    hotelRequests: [],
    editing: false,
    edited: null,
    loading: false
  }),
  computed: {
    ...mapGetters([
      'event'
    ])
  },
  mounted () {
    this.load()
  },
  methods: {
    async load () {
      this.loading = true
      this.hotelRequests = await get('/api/event/' + this.event.id + '/hotel/submitted_requests')
      this.loading = false
    },
    edit (data) {
      console.log('Editing ' + data.id)
      this.edited = data.id
      this.editing = true
    },
    cancel () {
      this.editing = false
      this.edited = null
    },
    save () {
      this.$refs.form.save().then(() => {
        this.editing = false
        this.edited = null
        this.load()
      })
    }
  },
  watch: {
    event () {
      this.load()
    }
  }
}
</script>
