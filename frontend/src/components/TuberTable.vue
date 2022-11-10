<template>
    <div>
        <Toast />
        <ConfirmPopup></ConfirmPopup>
        <div class="flex justify-content-between">
            <h3>{{ tableTitle }}</h3>
            <slot name="controls" :add="add">
                    <Button @click="add">Add</Button>
            </slot>
        </div>
        <DataTable :value="formattedInstances" :loading="loading" dataKey="id" class="p-datatable-sm" ref="dt"
            :paginator="true" :rows="rows"
            :lazy="true" :totalRecords="totalRecords" @page="onPage($event)" @sort="onSort($event)"
            :filterDisplay="filterDisplay" @filter="onFilter($event)" :filters="filters"
        >
            <slot name="columns"></slot>
            <slot name="actions" :edit="edit" :remove="remove">
                <Column header="Actions" style="width: 10rem">
                    <template #body="slotProps">
                        <Button @click="edit(slotProps.data)" icon="pi pi-cog" class="p-button-info" />
                        <Button @click="remove($event, slotProps.data)" icon="pi pi-times" class="p-button-danger ml-2" />
                    </template>
                </Column>
            </slot>
        </DataTable>

        <Dialog v-model:visible="editing">
            <template #header>
                <h3>{{ formTitle }}</h3>
            </template>

            <slot name="form" :modelValue="edited" @update:modelValue="edited=event.target.value" @save="save(edited)" @cancel="cancel"></slot>

            <template #footer>
                <slot name="formActions" :edited="edited" :save="save" :cancel="cancel">
                    <Button label="Cancel" @click="cancel" icon="pi pi-times" class="p-button-text"/>
                    <Button label="Save" @click="save(edited)" icon="pi pi-check" autofocus />
                </slot>
            </template>
        </Dialog>
    </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { get, patch, del, post } from '@/lib/rest'

export default {
  name: 'TuberTable',
  props: {
    url: {
      type: String,
      required: true
    },
    tableTitle: {
      type: String,
      required: true
    },
    formTitle: {
      type: String,
      required: true
    },
    format: {
      type: Function,
      default (data) {
        return data
      }
    },
    parameters: {
      type: Object,
      default () {
        return {}
      }
    },
    autoload: {
      type: Boolean,
      default () {
        return true
      }
    },
    rows: {
      type: Number,
      default () {
        return 25
      }
    },
    filters: {
      type: Object
    },
    filterDisplay: {
      type: String,
      default () {
        return 'row'
      }
    }
  },
  components: {
  },
  data: () => ({
    instances: [],
    formattedInstances: [],
    editing: false,
    edited: null,
    loading: false,
    totalRecords: 0,
    lazyParams: {}
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    fullUrl () {
      return this.url.replace('<event>', this.event.id)
    },
    eventSpecific () {
      return this.url.includes('<event>')
    }
  },
  mounted () {
    this.lazyParams = {
      first: 0,
      rows: this.rows,
      sortField: 'id',
      sortOrder: 1,
      filters: this.filters
    }
    if (this.autoload && this.event) {
      this.load()
    }
  },
  methods: {
    async load () {
      this.loading = true
      const paginationParams = {
        offset: this.lazyParams.first,
        limit: this.lazyParams.rows
      }
      if (this.lazyParams.sortField) {
        paginationParams.sort = this.lazyParams.sortField
        paginationParams.order = this.lazyParams.sortOrder > 0 ? 'asc' : 'desc'
      }
      for (const filter in this.lazyParams.filters) {
        if (this.lazyParams.filters[filter].value) {
          paginationParams.search_field = filter
          paginationParams.search = this.lazyParams.filters[filter].value
          paginationParams.search_mode = this.lazyParams.filters[filter].matchMode
        }
      }
      Object.assign(paginationParams, this.parameters)
      this.instances = await get(this.fullUrl, paginationParams)
      paginationParams.count = true
      this.totalRecords = await get(this.fullUrl, paginationParams)
    },
    edit (instance) {
      this.edited = instance
      this.editing = true
    },
    async add () {
      const newmodel = await post(this.fullUrl)
      this.edited = newmodel
      this.editing = true
    },
    cancel () {
      this.editing = false
      this.edited = null
    },
    async save (data) {
      await patch(this.fullUrl + '/' + data.id, data)
      this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 1000 })
      this.editing = false
      this.edited = null
      this.load()
    },
    async remove (event, data) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'Are you sure you want to delete this?',
        icon: 'pi pi-exclamation-triangle',
        accept: async () => {
          await del(this.fullUrl + '/' + data.id)
          this.$toast.add({ severity: 'success', summary: 'Deleted Successfully', life: 1000 })
          this.editing = false
          this.edited = null
          this.load()
        },
        reject: () => {
        }
      })
    },
    onPage (event) {
      this.lazyParams = event
      this.load()
    },
    onSort (event) {
      this.lazyParams = event
      this.load()
    },
    onFilter (event) {
      this.lazyParams = event
      this.load()
    }
  },
  watch: {
    event () {
      if (this.eventSpecific) {
        this.load()
      }
    },
    instances () {
      if (this.instances.length > 0) {
        Promise.resolve(this.format(this.instances)).then((formatted) => {
          this.formattedInstances = formatted
          this.loading = false
        })
      } else {
        this.formattedInstances = []
        this.loading = false
      }
    },
    parameters () {
      this.load()
    }
  }
}
</script>