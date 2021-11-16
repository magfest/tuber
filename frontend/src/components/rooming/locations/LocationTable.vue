<template>
    <div>
        <DataTable :value="hotelLocations">
          <Column field="name" header="Name"></Column>
          <Column field="address" header="Address"></Column>
          <Column header="Actions">
              <template #body="slotProps">
                  <Button @click="remove($event, slotProps.data)" icon="pi pi-times" class="p-button-rounded p-button-danger" />
                  <Button @click="edit(slotProps.data)" icon="pi pi-cog" class="p-button-rounded" />
              </template>
          </Column>
        </DataTable>
        <Button @click="editing=true">Add</Button>

        <Dialog v-model:visible="editing">
            <template #header>
                <h3>Hotel Location</h3>
            </template>

            <location-form :id="edited" ref="form" />

            <template #footer>
                <Button label="Cancel" @click="cancel" icon="pi pi-times" class="p-button-text"/>
                <Button label="Save" @click="save" icon="pi pi-check" autofocus />
            </template>
        </Dialog>
    </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { get, del } from '@/lib/rest'
import LocationForm from './LocationForm.vue'

export default {
  name: 'LocationTable',
  props: [
  ],
  components: {
    LocationForm
  },
  data: () => ({
    hotelLocations: [],
    editing: false,
    edited: null
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
    load () {
      get('/api/event/' + this.event.id + '/hotel_location').then((hotelLocations) => {
        this.hotelLocations = hotelLocations
      })
    },
    remove (event, data) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'Are you sure?',
        icon: 'pi pi-exclamation-triangle',
        accept: () => {
          del('/api/event/' + this.event.id + '/hotel_location/' + data.id).then(() => {
            this.$toast.add({ severity: 'success', summary: 'Deleted Successfully', life: 300 })
            this.load()
          }).catch(() => {
            this.$toast.add({ severity: 'error', summary: 'Deletion Failed', detail: 'Please contact your server administrator for assistance.', life: 300 })
          })
        }
      })
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
