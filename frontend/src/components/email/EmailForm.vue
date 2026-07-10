<template>
    <form @submit.prevent class="email-form">
        <TabView>
            <TabPanel header="Configuration">
                <div class="formgrid grid">
                    <div class="field col-12 md:col-6">
                        <label for="name">Name</label><br />
                        <InputText v-model="data.name" id="name" type="text" placeholder="New Email" class="w-full" />
                    </div>
                    <div class="field col-12 md:col-6">
                        <label for="description">Description</label><br />
                        <InputText v-model="data.description" id="description" type="text"
                                   placeholder="Describe this email" class="w-full" />
                    </div>
                    <div class="field col-12 md:col-6">
                        <label for="source">Source</label><br />
                        <Dropdown id="source" v-model="data.source" :options="sources" optionLabel="name"
                                  optionValue="id" class="w-full" placeholder="Pick a sender" />
                    </div>
                    <div class="field col-12 md:col-6 flags">
                        <div class="field-checkbox">
                            <Checkbox id="active" v-model="data.active" :binary="true" />
                            <label for="active">Active</label>
                        </div>
                        <div class="field-checkbox">
                            <Checkbox id="send_once" v-model="data.send_once" :binary="true" />
                            <label for="send_once">Send Once</label>
                        </div>
                    </div>
                </div>
            </TabPanel>

            <TabPanel>
                <template #header>
                    <span>Filter</span>
                    <Tag v-if="preview" class="ml-2" :severity="filterSeverity"
                         :value="preview.matched_count + '/' + preview.total" />
                </template>
                <p class="hint">Lua code that returns a <code>function(context)</code> deciding who receives
                   this email. The evaluation below runs live against this event's attendees.</p>
                <code-editor v-model="data.code" language="lua" :rows="12"
                             placeholder="return function(context)&#10;    return context.hotel_request.declined ~= true&#10;end"
                             @update:modelValue="schedulePreview('filter')" />
                <div class="filter-results">
                    <ProgressSpinner v-if="filterLoading" class="spinner" strokeWidth="6" />
                    <template v-if="preview">
                        <Tag :severity="filterSeverity"
                             :value="preview.matched_count + ' of ' + preview.total + ' attendees match'" />
                        <SelectButton v-model="showMode" :options="showModes" optionLabel="label"
                                      optionValue="value" :allowEmpty="false" />
                        <span v-for="error in preview.filter_errors" :key="error" class="error-text">{{ error }}</span>
                        <span v-if="preview.truncated" class="hint">
                            Showing the first 1000; {{ preview.truncated }} more not listed.
                        </span>
                    </template>
                    <span v-else-if="filterLoading" class="hint">Evaluating…</span>
                </div>
                <DataTable v-if="preview" :value="preview.attendees" class="p-datatable-sm"
                           :paginator="preview.attendees.length > 10" :rows="10" dataKey="id">
                    <template #empty>
                        {{ showMode === 'matched' ? 'Nobody matches this filter.' : 'Everybody matches this filter.' }}
                    </template>
                    <Column field="name" header="Name" :sortable="true"></Column>
                    <Column field="email" header="Email"></Column>
                    <Column v-for="symbol in preview.symbols" :key="symbol" :header="'context.' + symbol">
                        <template #body="slotProps">
                            <code class="var-value">{{ formatVar(slotProps.data.pertinent[symbol]) }}</code>
                        </template>
                    </Column>
                </DataTable>
            </TabPanel>

            <TabPanel header="Email Text">
                <div class="grid">
                    <div class="col-12 lg:col-6">
                        <div class="field">
                            <label for="subject">Subject Template</label><br />
                            <InputText v-model="data.subject" id="subject" type="text" placeholder="Please Read"
                                       class="w-full code" @update:modelValue="schedulePreview('render')" />
                        </div>
                        <div class="field">
                            <label for="body">Body Template</label><br />
                            <code-editor v-model="data.body" language="django" :rows="18"
                                         placeholder="Hello ..." @update:modelValue="schedulePreview('render')" />
                        </div>
                    </div>
                    <div class="col-12 lg:col-6">
                        <div class="field">
                            <label>Preview as</label><br />
                            <Dropdown v-model="previewBadge" :options="previewOptions" optionLabel="name"
                                      optionValue="id" class="w-full" placeholder="First matched attendee"
                                      :showClear="previewBadge !== null"
                                      @update:modelValue="runPreview('render')" />
                        </div>
                        <div class="rendered" v-if="preview && preview.preview">
                            <div class="rendered-busy" v-if="renderLoading">
                                <ProgressSpinner class="spinner-lg" strokeWidth="5" />
                            </div>
                            <div class="rendered-heading">
                                To: {{ preview.preview.name }} &lt;{{ preview.preview.email }}&gt;
                            </div>
                            <p v-if="preview.render_error" class="error-text">{{ preview.render_error }}</p>
                            <template v-else>
                                <div class="rendered-subject">{{ preview.preview.subject || '(no subject)' }}</div>
                                <div class="rendered-body">{{ preview.preview.body }}</div>
                            </template>
                        </div>
                        <p v-else-if="preview && !preview.matched_count" class="hint">
                            Nobody matches the filter yet — the preview appears once someone does,
                            or pick an attendee above.
                        </p>
                        <Panel v-if="preview && preview.variables" header="Available variables" :toggleable="true"
                               :collapsed="true" class="mt-3">
                            <div v-for="(value, key) in preview.variables" :key="key" class="var-row">
                                <code class="var-name">{{ key }}</code>
                                <code class="var-value">{{ formatVar(value) }}</code>
                            </div>
                        </Panel>
                    </div>
                </div>
            </TabPanel>
        </TabView>
    </form>
</template>

<style scoped>
.flags {
  padding-top: 1.6rem;
}
.hint {
  color: var(--text-color-secondary, #6c757d);
  font-size: 0.9rem;
  margin-top: 0;
}
.code {
  font-family: monospace;
}
.filter-results {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin: 0.5rem 0;
}
.error-text {
  color: var(--red-600, #dc2626);
}
.rendered {
  position: relative;
  border: 1px solid var(--surface-border, #dee2e6);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  background: var(--surface-50, #fafafa);
}
.rendered-busy {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(128, 128, 128, 0.15);
  border-radius: 6px;
  z-index: 1;
}
.rendered-heading {
  color: var(--text-color-secondary, #6c757d);
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}
.rendered-subject {
  font-weight: 700;
  border-bottom: 1px solid var(--surface-border, #dee2e6);
  padding-bottom: 0.4rem;
  margin-bottom: 0.6rem;
}
.rendered-body {
  white-space: pre-wrap;
  word-break: break-word;
}
.spinner {
  width: 1.3rem;
  height: 1.3rem;
}
.spinner-lg {
  width: 2.5rem;
  height: 2.5rem;
}
.var-row {
  display: flex;
  gap: 0.75rem;
  padding: 0.15rem 0;
  border-bottom: 1px solid var(--surface-border, #dee2e6);
}
.var-name {
  min-width: 11rem;
  font-weight: 600;
}
.var-value {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.85rem;
}
</style>

<script>
import { mapGetters } from 'vuex'
import ProgressSpinner from 'primevue/progressspinner'
import SelectButton from 'primevue/selectbutton'
import { get, post } from '../../lib/rest'
import CodeEditor from '../CodeEditor.vue'

export default {
  name: 'EmailForm',
  components: {
    CodeEditor,
    ProgressSpinner,
    SelectButton
  },
  props: [
    'modelValue'
  ],
  data () {
    return {
      data: this.modelValue,
      sources: [],
      preview: null,
      previewBadge: null,
      showMode: 'matched',
      showModes: [
        { label: 'Matches', value: 'matched' },
        { label: 'Non-matches', value: 'unmatched' }
      ],
      filterLoading: false,
      renderLoading: false,
      previewTimer: null,
      pendingKind: null
    }
  },
  computed: {
    ...mapGetters([
      'event'
    ]),
    filterSeverity () {
      if (!this.preview) {
        return 'info'
      }
      if (this.preview.filter_errors.length) {
        return 'danger'
      }
      return this.preview.matched_count ? 'success' : 'warning'
    },
    previewOptions () {
      return this.preview ? this.preview.attendees : []
    },
    renderBadge () {
      if (this.previewBadge) {
        return this.previewBadge
      }
      if (this.preview && this.preview.preview) {
        return this.preview.preview.badge
      }
      return null
    }
  },
  mounted () {
    if (this.event) {
      this.load()
    }
  },
  unmounted () {
    clearTimeout(this.previewTimer)
  },
  methods: {
    async load () {
      if (!this.event) {
        return
      }
      this.sources = await get('/api/event/' + this.event.id + '/email_source')
      this.runPreview('filter')
    },
    formatVar (value) {
      if (value === null || value === undefined) {
        return 'nil'
      }
      if (typeof value === 'string') {
        return value
      }
      return JSON.stringify(value)
    },
    schedulePreview (kind) {
      // A pending filter evaluation must not be downgraded by a subsequent
      // template keystroke — escalate and keep the timer rolling.
      if (this.pendingKind !== 'filter') {
        this.pendingKind = kind
      }
      clearTimeout(this.previewTimer)
      this.previewTimer = setTimeout(() => {
        const kind = this.pendingKind
        this.pendingKind = null
        this.runPreview(kind)
      }, 700)
    },
    async runPreview (kind) {
      if (!this.event) {
        return
      }
      // Rendering against one attendee is cheap; the full filter pass over
      // every attendee only runs when the filter code itself changed.
      const renderOnly = kind === 'render' && this.renderBadge !== null
      if (renderOnly) {
        this.renderLoading = true
      } else {
        this.filterLoading = true
        this.renderLoading = true
      }
      try {
        const response = await post('/api/event/' + this.event.id + '/email/preview', {
          code: this.data.code || '',
          subject: this.data.subject || '',
          body: this.data.body || '',
          badge: this.renderBadge,
          show: this.showMode,
          evaluate_filter: !renderOnly
        })
        if (renderOnly && this.preview) {
          this.preview.preview = response.preview
          this.preview.variables = response.variables
          this.preview.render_error = response.render_error
        } else {
          this.preview = response
        }
      } catch (e) {
        // Leave the last good preview in place; the next edit retries.
      }
      this.filterLoading = false
      this.renderLoading = false
    }
  },
  watch: {
    event () {
      this.load()
    },
    showMode () {
      this.runPreview('filter')
    }
  }
}
</script>
