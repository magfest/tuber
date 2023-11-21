<template>
    <div class="card">
        <Toast />
        <h3>Server Actions</h3>
        <Button @click="import_shifts" label="Import Shifts"></Button>
    </div>
</template>

<style>

</style>

<script>
import { post } from '@/lib/rest'

export default {
  name: 'Actions',
  methods: {
    async import_shifts () {
        try {
            await post('/api/import_shifts')
            this.$toast.add({ severity: 'success', summary: 'Shifts Imported', life: 1000 })
        } catch {
            this.$toast.add({ severity: 'error', summary: 'Failed to import shifts', detail: 'Please contact your server administrator for assistance.', life: 3000 })
        }
    }
  }
}
</script>
