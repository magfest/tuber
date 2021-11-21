<template>
    <div>
        <DataTable :value="hotelRoomBlocks" :loading="loading">
            <Column field="name" header="Name"></Column>
            <Column field="description" header="Description"></Column>
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
                <h3>Room Block</h3>
            </template>

            <room-block-form :id="edited" ref="form" />

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
import RoomBlockForm from './RoomBlockForm.vue'

export default {
  name: 'RoomBlockTable',
  props: [
  ],
  components: {
    RoomBlockForm
  },
  data: () => ({
    hotelRoomBlocks: [],
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
      this.hotelRoomBlocks = await get('/api/event/' + this.event.id + '/hotel_room_block')
      this.loading = false
    },
    remove (event, data) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'Are you sure?',
        icon: 'pi pi-exclamation-triangle',
        accept: () => {
          del('/api/event/' + this.event.id + '/hotel_room_block/' + data.id).then(() => {
            this.$toast.add({ severity: 'success', summary: 'Deleted Successfully', life: 300 })
            this.load()
          }).catch(() => {
            this.$toast.add({ severity: 'error', summary: 'Deletion Failed', detail: 'Please contact your server administrator for assistance.', life: 300 })
          })
        }
      })
    },
    edit (data) {
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
