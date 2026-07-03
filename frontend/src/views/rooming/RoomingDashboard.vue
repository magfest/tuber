<template>
  <div class="card">
    <div class="flex justify-content-between align-items-center">
      <h3>Rooming Dashboard</h3>
      <Button icon="pi pi-refresh" class="p-button-text" @click="load" :loading="loading" />
    </div>

    <div v-if="data" class="grid">
      <div class="col-12 md:col-4">
        <div class="stat-card">
          <h4>Requests</h4>
          <div class="stat-big">{{ data.requests.percent_resolved }}%</div>
          <div class="stat-sub">of {{ data.requests.eligible }} eligible people resolved</div>
          <ul class="stat-list">
            <li><router-link :to="requestsLink('complete')">{{ data.requests.completed }} completed a request</router-link></li>
            <li><router-link :to="requestsLink('declined')">{{ data.requests.declined }} declined a room</router-link></li>
            <li><router-link :to="requestsLink('incomplete')">{{ data.requests.pending }} still pending</router-link></li>
          </ul>
        </div>
      </div>
      <div class="col-12 md:col-4">
        <div class="stat-card">
          <h4>Room Nights</h4>
          <div class="stat-big">{{ data.room_nights.assigned }}<span class="stat-of">/{{ data.room_nights.requested }}</span></div>
          <div class="stat-sub">nights assigned of requested</div>
          <ul class="stat-list">
            <li>{{ data.room_nights.requested }} requested</li>
            <li>{{ data.room_nights.approved }} approved</li>
            <li>{{ data.room_nights.assigned }} assigned</li>
            <li v-if="data.room_nights.roomless_assignments">
              {{ data.room_nights.roomless_assignments }} assigned without a room
            </li>
          </ul>
        </div>
      </div>
      <div class="col-12 md:col-4">
        <div class="stat-card">
          <h4>Rooms</h4>
          <div class="stat-big">{{ data.rooms.completed }}<span class="stat-of">/{{ data.rooms.total }}</span></div>
          <div class="stat-sub">rooms completed</div>
          <ul class="stat-list">
            <li v-if="data.rooms.suggested_pending">
              <router-link to="/rooming/assignments">{{ data.rooms.suggested_pending }} suggestions awaiting review</router-link>
            </li>
            <li>{{ data.rooms.incomplete }} in progress</li>
          </ul>
        </div>
      </div>

      <div class="col-12 md:col-6" v-if="data.rooms.by_block.length > 1">
        <h4>Rooms by Block</h4>
        <DataTable :value="data.rooms.by_block" class="p-datatable-sm">
          <Column field="name" header="Block"></Column>
          <Column field="total" header="Rooms"></Column>
          <Column field="completed" header="Completed"></Column>
          <Column field="suggested_pending" header="Suggestions Pending"></Column>
        </DataTable>
      </div>

      <div class="col-12" :class="{ 'md:col-6': data.rooms.by_block.length > 1 }">
        <h4>Remaining Issues</h4>
        <p v-if="!data.issues.length">
          <i class="pi pi-check-circle" style="color: var(--green-600, #16a34a)" />
          Nothing outstanding — the rooming system is in good shape.
        </p>
        <ul class="issues">
          <li v-for="issue in data.issues" :key="issue.kind">
            <router-link :to="issueLink(issue)">
              <i class="pi pi-exclamation-triangle mr-2" />
              <b>{{ issue.count }}</b> {{ issueLabel(issue) }}
            </router-link>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  border: 1px solid var(--surface-border, #dee2e6);
  border-radius: 8px;
  padding: 1rem;
  height: 100%;
}
.stat-card h4 {
  margin: 0 0 0.5rem 0;
}
.stat-big {
  font-size: 2.2rem;
  font-weight: 700;
}
.stat-of {
  font-size: 1.2rem;
  font-weight: 400;
  color: var(--text-color-secondary, #6c757d);
}
.stat-sub {
  color: var(--text-color-secondary, #6c757d);
  margin-bottom: 0.5rem;
}
.stat-list {
  margin: 0;
  padding-left: 1.2rem;
}
.issues {
  list-style: none;
  padding: 0;
}
.issues li {
  margin-bottom: 0.5rem;
}
.issues a {
  color: var(--text-color, inherit);
  text-decoration: none;
}
.issues a:hover {
  text-decoration: underline;
}
.issues .pi-exclamation-triangle {
  color: var(--orange-500, #f59e0b);
}
</style>

<script>
import { mapGetters } from 'vuex'
import { get } from '../../lib/rest'

const ISSUE_LABELS = {
  missing_shifts: 'people requested a restricted night without qualifying shifts',
  pending_manual_approvals: 'manual-approval nights awaiting a decision',
  unassigned_approved: 'people with approved nights not yet assigned',
  roomless_assignments: 'night assignments without a room',
  rooms_with_errors: 'completed rooms with unresolved issues',
  incomplete_requests: 'eligible people who have not finished a request',
  suggested_rooms_pending: 'suggested rooms awaiting review'
}

export default {
  name: 'RoomingDashboard',
  data: () => ({
    data: null,
    loading: false
  }),
  computed: {
    ...mapGetters([
      'event'
    ])
  },
  mounted () {
    this.load()
    window.addEventListener('detailmodal-changed', this.load)
  },
  unmounted () {
    window.removeEventListener('detailmodal-changed', this.load)
  },
  methods: {
    async load () {
      this.loading = true
      this.data = await get('/api/event/' + this.event.id + '/hotel/dashboard')
      this.loading = false
    },
    requestsLink (filter) {
      return { path: '/rooming/requests', query: { afilter: filter } }
    },
    issueLabel (issue) {
      return ISSUE_LABELS[issue.kind] || issue.kind
    },
    issueLink (issue) {
      const link = issue.link || {}
      if (link.page === 'requests') {
        return { path: '/rooming/requests', query: { afilter: link.filter } }
      }
      if (link.page === 'approvals') {
        return { path: '/rooming/approvals' }
      }
      if (link.page === 'assignments') {
        const query = {}
        if (issue.rooms && issue.rooms.length === 1) {
          query.room = String(issue.rooms[0])
        }
        return { path: '/rooming/assignments', query }
      }
      return { path: '/rooming' }
    }
  },
  watch: {
    event () {
      this.load()
    }
  }
}
</script>
