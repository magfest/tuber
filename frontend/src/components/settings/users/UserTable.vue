<template>
  <div>
    <tuber-table tableTitle="Users" formTitle="User" url="/api/user" :filters="filters">
      <template #columns>
        <Column field="username" filterField="username" header="Username" :sortable="true">
          <template #filter="{ filterModel, filterCallback }">
            <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"
              :placeholder="`Search by Username`" v-tooltip.top.focus="'Hit enter key to filter'" />
          </template>
        </Column>
        <Column field="email" filterField="email" header="Email" :sortable="true">
          <template #filter="{ filterModel, filterCallback }">
            <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"
              :placeholder="`Search by Email`" v-tooltip.top.focus="'Hit enter key to filter'" />
          </template>
        </Column>
        <Column field="active" header="Active" :sortable="true" style="width: 8rem">
          <template #body="slotProps">
            <i class="pi pi-check" v-if="slotProps.data.active" />
            <i class="pi pi-times" v-else />
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <TriStateCheckbox v-model="filterModel.value" @change="filterCallback()" class="p-column-filter" />
          </template>
        </Column>
      </template>

      <template #form="props">
        <user-form :modelValue="props.modelValue" />
      </template>

      <template #formActions="props">
        <Button label="Cancel" @click="props.cancel" icon="pi pi-times" class="p-button-text" />
        <Button label="Save" @click="save(props.edited, props.cancel)" icon="pi pi-check" autofocus />
      </template>
    </tuber-table>
  </div>
</template>

<script>
import UserForm from './UserForm.vue'
import TuberTable from '../../TuberTable.vue'
import { FilterMatchMode } from 'primevue/api'
import { post, patch } from '@/lib/rest'

export default {
  name: 'UserTable',
  components: {
    UserForm,
    TuberTable
  },
  data: () => ({
    filters: {
      username: { value: null, matchMode: FilterMatchMode.CONTAINS },
      email: { value: null, matchMode: FilterMatchMode.CONTAINS },
      active: { value: null, matchMode: FilterMatchMode.EQUALS }
    }
  }),
  methods: {
    async save (user, cancel) {
      try {
        let newuser = {}
        if (user.id) {
          newuser = await patch('/api/user/' + user.id, user)
        } else {
          newuser = await post('/api/user', user)
        }
        if (user.newPassword) {
          await post('/api/change_password/' + newuser.id, { password: user.newPassword })
        }
        cancel()
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', life: 300 })
      } catch (error) {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: 'Please contact your server administrator for assistance.', life: 300 })
      }
    }
  }
}
</script>
