<template>
  <v-tab-item>
    <v-form>
      <p>Import/Export data from/to a CSV file</p>
      <p>This form is very dangerous. You may wish to backup the database first.
        Note that this tool runs without regard to events! Doing a full import
        can blow <b>everything</b> away.
      </p>
      <v-select
        label="CSV Type"
        outlined
        v-model="csv_type"
        :items="csv_types"/>
      <v-file-input
        label="CSV Upload"
        v-model="files"
        accept=".csv"
        show-size
        outlined/>
      <v-checkbox
        v-model="raw_import"
        label="Raw Import (No input validation, No triggers will execute)"
      ></v-checkbox>
      <v-checkbox
        v-model="full_import"
        label="Import Whole Table (Will delete everything before importing)"
      ></v-checkbox>
      <v-card-actions>
        <v-spacer/>
        <v-btn
          outlined
          type="submit"
          @click.prevent="importCSV"
        >
          Import
        </v-btn>
        <v-btn
          outlined
          type="submit"
          @click.prevent="exportCSV"
        >
          Export
        </v-btn>
      </v-card-actions>
    </v-form>
  </v-tab-item>
</template>

<script>
export default {
  name: 'ImportFromCSV',
  data() {
    return {
      raw_import: false,
      full_import: false,
      csv_type: '',
      csv_types: [
        'Badge',
        'BadgeToDepartment',
        'Department',
        'BadgeType',
        'RibbonType',
        'RibbonToBadge',
        'Email',
        'EmailTrigger',
        'EmailSource',
        'EmailReceipt',
        'Event',
        'HotelRoomRequest',
        'HotelRoomBlock',
        'HotelRoom',
        'HotelRoommateRequest',
        'HotelAntiRoommateRequest',
        'HotelLocation',
        'HotelRoomNight',
        'RoomNightRequest',
        'RoomNightAssignment',
        'RoomNightApproval',
        'Schedule',
        'ScheduleEvent',
        'JobScheduleAssociation',
        'JobScheduleEventAssociation',
        'JobRoleAssociation',
        'Job',
        'Shift',
        'ShiftAssignment',
        'ShiftSignup',
        'User',
        'Session',
        'Permission',
        'Role',
        'Grant',
      ],
      files: [],
    };
  },

  methods: {
    importCSV() {
      const self = this;
      this.upload('/api/importer/csv', {
        csv_type: self.csv_type,
        raw_import: self.raw_import,
        full_import: self.full_import,
        files: self.files,
      }).then(() => {
        self.$store.commit('open_snackbar', 'CSV imported successfully.');
      }).catch(() => {
        self.$store.commit('open_snackbar', 'Failed to import CSV.');
      });
    },
    exportCSV() {
      const self = this;
      this.download('/api/importer/csv', {
        csv_type: self.csv_type,
      });
    },
  },
};
</script>

<style scoped>

</style>
