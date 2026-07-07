<template>
  <div class="card">
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <div class="flex justify-content-between align-items-center">
      <h3>Email Settings</h3>
      <Button label="Import from another event" icon="pi pi-download" class="p-button-outlined"
              @click="showImport = true" :disabled="importOptions.length === 0" />
    </div>
    <TabView>
        <TabPanel header="Emails">
            <email-table :key="'emails-' + reloadKey" />
        </TabPanel>
        <TabPanel header="Email Sources">
            <email-source-table :key="'sources-' + reloadKey" />
        </TabPanel>
        <TabPanel header="Email Receipts">
            <email-receipt-table />
        </TabPanel>
        <TabPanel header="Email Triggers">
            <email-trigger-table />
        </TabPanel>
    </TabView>

    <Dialog v-model:visible="showImport" modal header="Import Email Setup"
            :style="{ width: '30rem', maxWidth: '95vw' }">
      <p>Copy email templates and sources from another event into
         <b>{{ event ? event.name : '' }}</b>. Items with a name that already
         exists here are skipped, and everything imports <b>inactive</b> so
         nothing sends until you review it.</p>
      <div class="field">
        <label for="import-event">Import from</label><br>
        <Dropdown id="import-event" v-model="importEvent" :options="importOptions"
                  optionLabel="name" optionValue="id" placeholder="Pick an event" class="w-full" />
      </div>
      <div class="field-checkbox">
        <Checkbox id="import-emails" v-model="importEmails" :binary="true" />
        <label for="import-emails">Email templates</label>
      </div>
      <div class="field-checkbox">
        <Checkbox id="import-sources" v-model="importSources" :binary="true" />
        <label for="import-sources">Email sources (sender addresses and credentials)</label>
      </div>
      <template #footer>
        <Button label="Cancel" class="p-button-text" @click="showImport = false" />
        <Button label="Import" icon="pi pi-download" :loading="importing"
                :disabled="!importEvent || (!importEmails && !importSources)" @click="runImport" />
      </template>
    </Dialog>
  </div>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex'
import { post } from '../../lib/rest'
import { EmailTable, EmailSourceTable, EmailReceiptTable, EmailTriggerTable } from '../../components/email'

export default {
  name: 'EmailSettings',
  components: {
    EmailTable,
    EmailSourceTable,
    EmailReceiptTable,
    EmailTriggerTable
  },
  data: () => ({
    showImport: false,
    importEvent: null,
    importEmails: true,
    importSources: true,
    importing: false,
    reloadKey: 0
  }),
  computed: {
    ...mapGetters([
      'event',
      'events'
    ]),
    importOptions () {
      if (!this.event) {
        return []
      }
      return (this.events || []).filter((x) => x.id !== this.event.id)
    }
  },
  methods: {
    async runImport () {
      this.importing = true
      try {
        const result = await post('/api/event/' + this.event.id + '/email/import', {
          from_event: this.importEvent,
          emails: this.importEmails,
          sources: this.importSources
        })
        const skipped = result.skipped.length
        this.$toast.add({
          severity: 'success',
          summary: 'Import Complete',
          detail: 'Imported ' + result.emails + ' template(s) and ' + result.sources +
            ' source(s)' + (skipped ? ', skipped ' + skipped + ' existing item(s).' : '.'),
          life: 6000
        })
        this.showImport = false
        this.reloadKey += 1
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Import Failed', life: 3000 })
      }
      this.importing = false
    }
  }
}
</script>
