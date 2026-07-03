<template>
  <div class="card">
    <Toast />
    <div class="flex justify-content-between align-items-center flex-wrap gap-2">
      <h3 class="mt-0 mb-0">Room Night Approvals<span v-if="department.name"> — {{ department.name }}</span></h3>
      <Dropdown v-model="departmentID" :options="departments" optionLabel="name" optionValue="id"
                placeholder="Select a department" />
    </div>
    <p>
        Restricted nights are approved automatically when their shift criteria are met —
        an overlapping shift for <b>shift window</b> nights, or enough total hours for
        <b>shift hours</b> nights. <b>Manual approval</b> nights (and any night whose
        criteria aren't met) can be approved here:
        <TriStateCheckbox /> pending,
        <TriStateCheckbox :modelValue="true" /> approved by this department,
        <TriStateCheckbox :modelValue="false" /> rejected.
        Unrestricted nights are approved for everyone.
    </p>
    <DataTable :value="requests" :loading="loading">
        <Column headerStyle="width: 12em" field="name" header="Name" key="name">
            <template #body="slotProps">
                <attendee-name :badge-id="slotProps.data.id" :name="slotProps.data.name" />
            </template>
        </Column>
        <Column headerStyle="width: 6em" v-for="roomNight of roomNights" :key="roomNight.id"
                field="room_nights" :header="roomNight.name">
            <template #body="slotProps">
                <div v-if="nightStatus(slotProps.data, roomNight)" class="night-cell">
                    <template v-if="roomNight.restriction_mode === 'none'">
                        <i class="pi pi-check flag-on" title="Unrestricted night" />
                    </template>
                    <template v-else>
                        <i v-if="roomNight.restriction_mode === 'shift_window'" class="pi pi-briefcase"
                           :class="nightStatus(slotProps.data, roomNight).approved_by_shifts ? 'flag-on' : 'flag-bad'"
                           :title="nightStatus(slotProps.data, roomNight).approved_by_shifts
                             ? 'Covered by an overlapping shift' : 'No overlapping shift'" />
                        <Tag v-if="roomNight.restriction_mode === 'shift_hours'"
                             :severity="nightStatus(slotProps.data, roomNight).hours_met ? 'success' : 'warning'"
                             :value="nightStatus(slotProps.data, roomNight).hours_assigned + '/' + nightStatus(slotProps.data, roomNight).hours_required + 'h'" />
                        <TriStateCheckbox @change="approve(slotProps.data, roomNight.id)"
                                          v-model="slotProps.data.room_nights[String(roomNight.id)].approved" />
                    </template>
                </div>
            </template>
        </Column>
        <Column headerStyle="width: 8em" header="All Nights" key="allnights">
            <template #body="slotProps">
                <Button @click="approveAll(slotProps.data)" icon="pi pi-check" class="p-button-rounded" />
                <Button @click="rejectAll(slotProps.data)" icon="pi pi-times" class="p-button-rounded p-button-danger ml-1" />
            </template>
        </Column>
        <Column field="justification" header="Justification" key="justification"></Column>
    </DataTable>
  </div>
</template>

<style scoped>
.night-cell {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.flag-on { color: var(--green-600, #16a34a); }
.flag-bad { color: var(--red-500, #ef4444); }
</style>

<script>
import { mapGetters } from 'vuex'
import { get, post } from '../../lib/rest'
import AttendeeName from '../../components/rooming/modals/AttendeeName.vue'

export default {
  name: 'RoomApprovals',
  components: {
    AttendeeName
  },
  data: () => ({
    departmentID: null,
    department: {},
    departments: [],
    requests: [],
    roomNights: [],
    loading: false
  }),
  computed: {
    ...mapGetters([
      'event'
    ])
  },
  mounted () {
    this.loadDepartments()
  },
  methods: {
    async loadDepartments () {
      if (!this.event) {
        return
      }
      this.departments = await get('/api/event/' + this.event.id + '/department', { sort: 'name' })
      const fromQuery = parseInt(this.$route.query.department)
      if (fromQuery && this.departments.some((x) => x.id === fromQuery)) {
        this.departmentID = fromQuery
      } else if (this.departments.length) {
        this.departmentID = this.departments[0].id
      }
    },
    async load () {
      if (!this.departmentID) {
        return
      }
      this.loading = true
      this.department = this.departments.find((x) => x.id === this.departmentID) || {}
      this.roomNights = await get('/api/event/' + this.event.id + '/hotel_room_night',
        { sort: 'date', hidden: false })
      this.requests = await get('/api/event/' + this.event.id + '/hotel/requests/' + this.departmentID)
      this.loading = false
    },
    nightStatus (request, roomNight) {
      const status = request.room_nights[String(roomNight.id)]
      if (!status || !status.requested) {
        return null
      }
      return status
    },
    approve (request, roomNight) {
      post('/api/event/' + this.event.id + '/hotel/approve/' + this.departmentID, {
        room_night: roomNight,
        badge: request.id,
        approved: request.room_nights[String(roomNight)].approved
      }).then(() => {
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', detail: request.name, life: 1500 })
      }).catch(() => {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: request.name })
      })
    },
    setAll (request, approved) {
      const posts = []
      for (const [roomNight, status] of Object.entries(request.room_nights)) {
        if (!status.requested || status.mode === 'none') {
          continue
        }
        status.approved = approved
        posts.push(post('/api/event/' + this.event.id + '/hotel/approve/' + this.departmentID, {
          room_night: parseInt(roomNight),
          badge: request.id,
          approved
        }))
      }
      Promise.all(posts).then(() => {
        this.$toast.add({ severity: 'success', summary: 'Saved Successfully', detail: request.name, life: 1500 })
      }).catch(() => {
        this.$toast.add({ severity: 'error', summary: 'Save Failed.', detail: request.name })
      })
    },
    approveAll (request) {
      this.setAll(request, true)
    },
    rejectAll (request) {
      this.setAll(request, false)
    }
  },
  watch: {
    event () {
      this.loadDepartments()
    },
    departmentID (value) {
      const query = Object.assign({}, this.$route.query)
      if (value) {
        query.department = String(value)
      } else {
        delete query.department
      }
      if (JSON.stringify(query) !== JSON.stringify(this.$route.query)) {
        this.$router.replace({ query })
      }
      this.load()
    }
  }
}
</script>
