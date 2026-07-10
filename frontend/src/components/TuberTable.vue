<template>
  <div>
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <div class="flex justify-content-between">
      <h3>{{ tableTitle }}</h3>
      <SelectButton v-if="modes.length" :modelValue="mode" :options="modes" optionLabel="label"
                    optionValue="value" :allowEmpty="false" @update:modelValue="onModeChange" />
      <slot name="controls" :add="add">
        <Button v-if="showAdd" @click="add">Add</Button>
        <span v-else></span>
      </slot>
    </div>
    <DataTable :value="formattedInstances" :loading="isLoading" dataKey="id" class="p-datatable-sm" ref="dt"
      :paginator="true" :rows="rows" :lazy="true" :totalRecords="totalRecords" @page="onPage($event)"
      @sort="onSort($event)" :filterDisplay="filterDisplay" @filter="onFilter($event)" :filters="filters"
      v-model:selection="selection" @select-all-change="onSelectAllChange" :selectAll="selectAll" @row-select="onRowSelect" @row-unselect="onRowUnselect">
      <slot name="columns"></slot>
      <slot name="actions" :edit="edit" :remove="remove" v-if="showActions">
        <Column header="Actions" style="width: 10rem">
          <template #body="slotProps">
            <Button @click="edit(slotProps.data)" icon="pi pi-cog" class="p-button-info" />
            <Button @click="remove($event, slotProps.data)" icon="pi pi-times" class="p-button-danger ml-2" />
          </template>
        </Column>
      </slot>
    </DataTable>

    <Dialog v-model:visible="editing" :breakpoints="{ '1000px': '85vw', '500px': '95vw' }"
      :style="dialogStyle">
      <template #header>
        <h3>{{ formTitle }}</h3>
      </template>

      <slot name="form" :modelValue="edited" @update:modelValue="edited = event.target.value" @save="save(edited)"
        @cancel="cancel"></slot>

      <template #footer>
        <slot name="formActions" :edited="edited" :save="save" :cancel="cancel">
          <Button label="Cancel" @click="cancel" icon="pi pi-times" class="p-button-text" />
          <Button label="Save" @click="save(edited)" icon="pi pi-check" autofocus />
        </slot>
      </template>
    </Dialog>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import SelectButton from 'primevue/selectbutton'
import { get, patch, del, post } from '../lib/rest'

export default {
  name: 'TuberTable',
  components: {
    SelectButton
  },
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
    },
    onSelect: {
      type: Function,
      default (data) {
        return data
      }
    },
    onRowSelect: {
      type: Function,
      default (data) {
      }
    },
    onRowUnselect: {
      type: Function,
      default (data) {
      }
    },
    showActions: {
      type: Boolean,
      default () {
        return true
      }
    },
    neverload: {
      type: Boolean,
      default () {
        return false
      }
    },
    loading: {
      type: Boolean,
      default () {
        return false
      }
    },
    // The endpoint returns {results, count} in one call instead of a bare
    // list plus a second count=true request.
    envelope: {
      type: Boolean,
      default () {
        return false
      }
    },
    // Server-side filter modes rendered as a SelectButton in the header,
    // passed to the endpoint as `modeParam`.
    modes: {
      type: Array,
      default () {
        return []
      }
    },
    modeParam: {
      type: String,
      default () {
        return 'filter'
      }
    },
    defaultMode: {
      type: String,
      default () {
        return ''
      }
    },
    // Mirror table state (mode, search, offset) into $route.query under this
    // prefix so filtered views are shareable and survive reloads.
    routeSync: {
      type: String,
      default () {
        return ''
      }
    },
    showAdd: {
      type: Boolean,
      default () {
        return true
      }
    },
    dialogStyle: {
      type: Object,
      default () {
        return { width: '50vw' }
      }
    }
  },
  data: () => ({
    instances: [],
    formattedInstances: [],
    editing: false,
    edited: null,
    isLoading: false,
    totalRecords: 0,
    lazyParams: {},
    selection: [],
    selectAll: false,
    mode: ''
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    fullUrl () {
      if (this.url.includes('<event>')) {
        return this.url.replace('<event>', this.event.id)
      }
      return this.url
    },
    eventSpecific () {
      return this.url.includes('<event>')
    }
  },
  mounted () {
    this.mode = this.defaultMode || (this.modes.length ? this.modes[0].value : '')
    this.lazyParams = {
      first: 0,
      rows: this.rows,
      sortField: 'id',
      sortOrder: 1,
      filters: this.filters
    }
    if (this.routeSync) {
      const query = this.$route.query
      const mode = query[this.routeSync + 'filter']
      if (mode && (!this.modes.length || this.modes.some((x) => x.value === mode))) {
        this.mode = mode
      }
      if (query[this.routeSync + 'offset']) {
        this.lazyParams.first = parseInt(query[this.routeSync + 'offset']) || 0
      }
    }
    if (this.autoload && (this.event || !this.eventSpecific)) {
      this.load()
    }
  },
  methods: {
    async load () {
      if (this.neverload) {
        return
      }
      this.isLoading = true
      const paginationParams = {
        offset: this.lazyParams.first,
        limit: this.lazyParams.rows
      }
      if (this.lazyParams.sortField) {
        paginationParams.sort = this.lazyParams.sortField
        paginationParams.order = this.lazyParams.sortOrder > 0 ? 'asc' : 'desc'
      }
      for (const filter in this.lazyParams.filters) {
        if (this.lazyParams.filters[filter].value || this.lazyParams.filters[filter].value === false) {
          paginationParams.search_field = filter
          paginationParams.search = this.lazyParams.filters[filter].value
          paginationParams.search_mode = this.lazyParams.filters[filter].matchMode
        }
      }
      Object.assign(paginationParams, this.parameters)
      if (this.modes.length || this.mode) {
        paginationParams[this.modeParam] = this.mode
      }
      if (this.envelope) {
        const data = await get(this.fullUrl, paginationParams)
        this.instances = data.results
        this.totalRecords = data.count
      } else {
        this.instances = await get(this.fullUrl, paginationParams)
        paginationParams.count = true
        this.totalRecords = await get(this.fullUrl, paginationParams)
      }
      this.syncRoute()
    },
    onModeChange (mode) {
      this.mode = mode
      this.lazyParams.first = 0
      this.load()
    },
    syncRoute () {
      if (!this.routeSync) {
        return
      }
      const query = Object.assign({}, this.$route.query)
      const set = (key, value) => {
        if (value) {
          query[this.routeSync + key] = String(value)
        } else {
          delete query[this.routeSync + key]
        }
      }
      set('filter', this.mode)
      set('offset', this.lazyParams.first)
      if (JSON.stringify(query) !== JSON.stringify(this.$route.query)) {
        this.$router.replace({ query })
      }
    },
    edit (instance) {
      this.edited = instance
      this.editing = true
    },
    async add () {
      try {
        const newmodel = await post(this.fullUrl)
        this.edited = newmodel
        this.editing = true
      } catch {
        this.$toast.add({ severity: 'error', summary: 'Failed to add ' + this.formTitle })
      }
    },
    cancel () {
      this.editing = false
      this.edited = null
    },
    async save (data) {
      try {
        await patch(this.fullUrl + '/' + data.id, data)
        this.editing = false
        this.edited = null
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 1000 })
      } catch {
        this.$toast.add({ severity: 'error', summary: 'Failed to save ' + this.formTitle + '(' + data.id + ')' })
      }
      this.load()
    },
    async remove (event, data) {
      this.$confirm.require({
        target: event.currentTarget,
        message: 'Are you sure you want to delete this?',
        icon: 'pi pi-exclamation-triangle',
        accept: async () => {
          try {
            await del(this.fullUrl + '/' + data.id)
            this.$toast.add({ severity: 'success', summary: 'Deleted Successfully', life: 1000 })
            this.editing = false
            this.edited = null
          } catch (ex) {
            console.log(ex, ex.message)
            this.$toast.add({ severity: 'error', summary: 'Failed to delete ' + this.formTitle, detail: ex.message })
          }
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
    },
    onSelectAllChange (event) {
      this.selectAll = !this.selectAll
    }
  },
  watch: {
    event () {
      // On logout the event becomes null; an event-specific table has
      // nothing to load (and would crash building its URL).
      if (this.eventSpecific && this.event) {
        this.load()
      }
    },
    // The url can embed path parameters (e.g. the selected hotel block), so a
    // change means a different dataset: restart from the first page.
    url () {
      this.lazyParams.first = 0
      this.selection = []
      this.load()
    },
    instances () {
      if (this.instances.length > 0) {
        Promise.resolve(this.format(this.instances)).then((formatted) => {
          this.formattedInstances = formatted
          this.isLoading = false
        })
      } else {
        this.formattedInstances = []
        this.isLoading = false
      }
    },
    parameters () {
      this.load()
    },
    selection () {
      this.onSelect(this.selection)
    },
    loading () {
      this.isLoading = this.loading
    }
  }
}
</script>
