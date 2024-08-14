<template>
    <div class="card">
        <Toast />
        <h3>Server Actions</h3>
        <Button @click="import_shifts" label="Import Shifts"></Button><br /><br />
        <Button @click="sync_attendees" label="Sync Attendees"></Button><br /><br />
        <Button @click="export_rooms" label="Export Rooms to Uber"></Button><br /><br />
    </div>
</template>

<style>

</style>

<script>
import { post } from '@/lib/rest'
import { mapGetters } from 'vuex'

export default {
  name: 'Actions',
  computed: {
    ...mapGetters([
        'event'
    ])
  },
  methods: {
    async import_shifts () {
        console.log(this.event);
        try {
            await post('/api/event/' + this.event.id + '/uber/import_shifts')
            this.$toast.add({ severity: 'success', summary: 'Shifts Imported', life: 1000 })
        } catch {
            this.$toast.add({ severity: 'error', summary: 'Failed to import shifts', detail: 'Please contact your server administrator for assistance.', life: 3000 })
        }
    },
    async sync_attendees () {
        try {
            await post('/api/event/' + this.event.id + '/uber/sync_attendees')
            this.$toast.add({ severity: 'success', summary: 'Attendees Synced', life: 1000 })
        } catch {
            this.$toast.add({ severity: 'error', summary: 'Failed to sync attendees', detail: 'Please contact your server administrator for assistance.', life: 3000 })
        }
    },
    async export_rooms () {
        try {
            await post('/api/event/' + this.event.id + '/uber/export_rooms')
            this.$toast.add({ severity: 'success', summary: 'Rooms Exported', life: 1000 })
        } catch {
            this.$toast.add({ severity: 'error', summary: 'Failed to export rooms', detail: 'Please contact your server administrator for assistance.', life: 3000 })
        }
    }
  }
}
</script>
