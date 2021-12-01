<template>
  <div class="card">
    <Toast />
    <ConfirmPopup></ConfirmPopup>
    <h3>Email Settings</h3>
    <TabView>
        <TabPanel header="Emails">
            <email-table />
        </TabPanel>
        <TabPanel header="Email Sources">
            <email-source-table />
        </TabPanel>
        <TabPanel header="Email Receipts">
            <email-receipt-table />
        </TabPanel>
        <TabPanel header="Email Triggers">
            <email-trigger-table />
        </TabPanel>
    </TabView>
  </div>
</template>

<style>
</style>

<script>
import { EmailTable, EmailSourceTable, EmailReceiptTable, EmailTriggerTable } from '../../components/email'

export default {
  name: 'EmailSettings',
  components: {
    EmailTable,
    EmailSourceTable,
    EmailReceiptTable,
    EmailTriggerTable
  }
}
</script>
