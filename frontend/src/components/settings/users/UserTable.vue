<template>
    <div>
        <DataTable :value="users" :loading="loading">
          <Column field="username" header="Username"></Column>
          <Column field="email" header="Email"></Column>
          <Column field="active" header="Active">
            <template #body="slotProps">
                <i class="pi pi-check" v-if="slotProps.data.active" />
                <i class="pi pi-times" v-else />
            </template>
          </Column>
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
                <h3>User</h3>
            </template>

            <user-form :id="edited" ref="form" />

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
import UserForm from './UserForm.vue'

export default {
  name: 'UserTable',
  props: [
  ],
  components: {
    UserForm
  },
  data: () => ({
    users: [],
    editing: false,
    edited: null,
    loading: false
  }),
  computed: {
    ...mapGetters([
    ])
  },
  mounted () {
    this.load()
  },
  methods: {
    async load () {
      this.loading = true
      this.users = await get('/api/user')
      this.loading = false
    },
    remove (event, data) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'Are you sure?',
        icon: 'pi pi-exclamation-triangle',
        accept: () => {
          del('/api/user/' + data.id).then(() => {
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
  }
}
</script>
