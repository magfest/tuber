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
          <div class="stat-big">{{ data.room_nights.assigned }}<span class="stat-of">/{{ data.room_nights.approved }}</span></div>
          <div class="stat-sub">nights assigned of approved</div>
          <ul class="stat-list">
            <li>{{ data.room_nights.requested }} requested</li>
            <li>{{ data.room_nights.approved }} approved</li>
            <li>{{ data.room_nights.assigned }} assigned</li>
            <li v-if="data.room_nights.roomless_assignments">
              <router-link :to="{ path: '/rooming/requests', query: { afilter: 'unassigned_approved' } }">
                {{ data.room_nights.roomless_assignments }} assigned without a room
              </router-link>
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

    <div v-if="matchStats.length" class="match-outlook">
      <div class="flex justify-content-between align-items-center flex-wrap gap-2">
        <h3 class="mb-0">Matching Outlook</h3>
        <div class="flex gap-2">
          <Dropdown v-if="matchStats.length > 1" v-model="matchBlock" :options="matchStats"
                    optionLabel="name" optionValue="id" title="Hotel block" />
          <Dropdown v-model="matchNights" :options="matchNightsOptions" optionLabel="label" optionValue="value"
                    title="Approved: only nights each person is approved for. Requested: every night they asked for." />
        </div>
      </div>
      <p class="hint">How well the open requests in this block could fit into rooms of {{ roomSize }},
        from their nights, roommate and gender answers alone — not the rooms built so far.</p>

      <div v-if="block" class="grid">
        <div class="col-12 lg:col-4">
          <div class="stat-card">
            <h4>Nights</h4>
            <div class="stat-big">{{ block.nights.room_night_floor }}</div>
            <div class="stat-sub">fewest room-nights possible for {{ block.nights.people }} people</div>
            <ul class="stat-list">
              <li title="Rooms only ever hold people with identical nights">
                {{ block.nights.exact_pattern_room_nights }} room-nights if every room had identical nights
                (<b>{{ percentOver(block.nights.exact_pattern_room_nights, block.nights.room_night_floor) }}</b>)
              </li>
              <li>{{ block.booked_room_nights }} room-nights booked in rooms so far</li>
              <li>{{ block.nights.floor_occupancy }}% of beds filled at the minimum</li>
              <li>{{ block.nights.average_nights }} nights per person on average</li>
              <li>{{ block.nights.distinct_patterns }} different night patterns;
                the top 3 cover {{ block.nights.top3_share }}% of people</li>
              <li>{{ block.nights.unique_patterns }} people share their nights with no one</li>
              <li title="Left over after filling whole rooms with people on identical nights">
                {{ block.nights.pattern_leftovers }} people left over after identical-night rooms</li>
              <li v-if="block.no_eligible_nights">Not counted: {{ block.no_eligible_nights }} with nights requested
                but none approved</li>
              <li v-if="block.no_nights_requested">Not counted: {{ block.no_nights_requested }} with no nights
                requested</li>
            </ul>
          </div>
        </div>
        <div class="col-12 lg:col-4">
          <div class="stat-card">
            <h4>Roommate Requests</h4>
            <div class="stat-big">{{ block.roommates.mutual_pairs }}</div>
            <div class="stat-sub">mutual pairs from {{ block.roommates.requests }} requests by
              {{ block.roommates.requesters }} people</div>
            <ul class="stat-list">
              <li>{{ block.roommates.one_way }} one-way requests within the block</li>
              <li v-for="(count, reason) in block.roommates.unplaceable" :key="reason">
                {{ count }} {{ unplaceableLabel(reason) }}
              </li>
              <li v-if="block.roommates.mutual_pairs">
                {{ block.roommates.pairs_identical_nights }} of {{ block.roommates.mutual_pairs }} mutual pairs
                want identical nights ({{ block.roommates.pairs_night_match }}% night match on average)
              </li>
              <li v-if="Object.keys(block.roommates.group_sizes).length">
                Request groups: {{ groupSizes(block.roommates.group_sizes) }}
              </li>
              <li v-if="block.roommates.oversized_groups" class="warn">
                {{ block.roommates.oversized_groups }} groups too big for one room
              </li>
              <li>{{ block.roommates.anti_requests }} anti-requests</li>
              <li v-if="block.roommates.conflicts" class="warn">
                {{ block.roommates.conflicts }} requests for someone who anti-requested them
              </li>
              <li>{{ block.roommates.prefer_department }} prefer roommates from their department</li>
            </ul>
          </div>
        </div>
        <div class="col-12 lg:col-4">
          <div class="stat-card">
            <h4>Single-Gender Rooms</h4>
            <div class="stat-big">{{ block.gender.requesters }}</div>
            <div class="stat-sub">people asked for a single-gender room</div>
            <table v-if="block.gender.buckets.length" class="mini-table">
              <thead>
                <tr><th>Gender</th><th>Asked</th><th title="Everyone in the block who gave this gender">Same gender</th></tr>
              </thead>
              <tbody>
                <tr v-for="bucket in block.gender.buckets" :key="bucket.gender">
                  <td>{{ bucket.gender }}<span v-if="!bucket.mapped" class="warn" title="Not in the gender map"> *</span></td>
                  <td>{{ bucket.requesters }}</td>
                  <td>{{ bucket.people }}</td>
                </tr>
              </tbody>
            </table>
            <ul class="stat-list">
              <li>{{ block.gender.blank }} people left gender blank (they can't share with these requesters)</li>
              <li v-if="block.gender.requesters_blank" class="warn">
                {{ block.gender.requesters_blank }} requesters left their own gender blank
              </li>
              <li v-if="block.gender.unmapped_answers.length">
                Not in the gender map: {{ block.gender.unmapped_answers.join(', ') }}
              </li>
            </ul>
          </div>
        </div>

        <div class="col-12 lg:col-6">
          <h4>People per Night</h4>
          <table class="mini-table nights-table">
            <thead>
              <tr><th></th><th v-for="night in block.nights.per_night" :key="night.id" :title="night.name">
                {{ night.name.slice(0, 2) }}</th></tr>
            </thead>
            <tbody>
              <tr><th>People</th><td v-for="night in block.nights.per_night" :key="night.id">{{ night.people }}</td></tr>
              <tr><th>Rooms</th><td v-for="night in block.nights.per_night" :key="night.id">{{ night.rooms }}</td></tr>
            </tbody>
          </table>
        </div>
        <div class="col-12 lg:col-6">
          <h4>Most Common Night Patterns</h4>
          <div v-for="(pattern, idx) in block.nights.top_patterns" :key="idx" class="pattern-row">
            <div class="night-tags">
              <Tag v-for="night in block.nights.per_night" :key="night.id" :value="night.name.slice(0, 2)"
                   :severity="pattern.nights.includes(night.id) ? 'success' : null" class="night-tag"
                   :class="{ 'night-tag-off': !pattern.nights.includes(night.id) }" />
            </div>
            <span>{{ pattern.people }} {{ pattern.people === 1 ? 'person' : 'people' }}</span>
          </div>
        </div>
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
.match-outlook {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border, #dee2e6);
}
.hint {
  color: var(--text-color-secondary, #6c757d);
  font-size: 0.9rem;
}
.warn {
  color: var(--orange-500, #f59e0b);
}
.mini-table {
  border-collapse: collapse;
  margin: 0.25rem 0 0.5rem 0;
}
.mini-table th, .mini-table td {
  padding: 0.2rem 0.6rem;
  text-align: right;
  border-bottom: 1px solid var(--surface-border, #dee2e6);
}
.mini-table th:first-child, .mini-table td:first-child {
  text-align: left;
}
.nights-table td, .nights-table thead th {
  text-align: center;
  padding: 0.2rem 0.4rem;
}
.pattern-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.3rem;
}
.night-tags {
  display: flex;
  gap: 0.1rem;
}
.night-tag {
  width: 1.4rem;
  padding: 0.1rem 0;
  font-size: 0.65rem;
}
.night-tag-off {
  background: var(--surface-400, #adb5bd);
  opacity: 0.4;
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
  unassigned_approved: 'people with nights ready to assign but no room',
  rooms_with_errors: 'completed rooms with unresolved issues',
  incomplete_requests: 'eligible people who have not finished a request',
  suggested_rooms_pending: 'suggested rooms awaiting review'
}

const UNPLACEABLE_LABELS = {
  no_request: 'requests for people with no room request',
  declined: 'requests for people who declined a room',
  other_block: 'requests for people in another block',
  no_eligible_nights: 'requests for people with no eligible nights'
}

export default {
  name: 'RoomingDashboard',
  data: () => ({
    data: null,
    loading: false,
    roomSize: 4,
    matchStats: [],
    matchBlock: null,
    matchNights: 'approved',
    matchNightsOptions: [
      { label: 'Approved nights', value: 'approved' },
      { label: 'Requested nights', value: 'requested' }
    ]
  }),
  computed: {
    ...mapGetters([
      'event'
    ]),
    block () {
      return this.matchStats.find((x) => x.id === this.matchBlock) || null
    }
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
      if (!this.event) {
        return
      }
      this.loading = true
      this.data = await get('/api/event/' + this.event.id + '/hotel/dashboard')
      await this.loadMatchStats()
      this.loading = false
    },
    async loadMatchStats () {
      if (!this.event) {
        return
      }
      this.matchStats = await get('/api/event/' + this.event.id + '/hotel/match_stats',
        { nights: this.matchNights })
      if (!this.matchStats.some((x) => x.id === this.matchBlock)) {
        // Default to the block with the most people in it.
        const busiest = [...this.matchStats].sort((a, b) => b.nights.people - a.nights.people)[0]
        this.matchBlock = busiest ? busiest.id : null
      }
    },
    percentOver (value, floor) {
      return floor ? '+' + Math.round((value - floor) / floor * 100) + '%' : '—'
    },
    unplaceableLabel (reason) {
      return UNPLACEABLE_LABELS[reason] || reason
    },
    groupSizes (sizes) {
      return Object.entries(sizes).map(([size, count]) => count + ' of ' + size).join(', ')
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
    },
    matchNights () {
      this.loadMatchStats()
    }
  }
}
</script>
