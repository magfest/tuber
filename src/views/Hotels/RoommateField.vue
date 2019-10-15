<template>
    <v-autocomplete
        v-model="roommates"
        :items="options"
        :loading="optionsLoading"
        :search-input.sync="search"
        hide-no-data
        item-text="text"
        item-value="id"
        :label="label"
        prepend-icon="person"
        append-icon=""
        :placeholder="placeholder"
        :disabled="disabled"
        multiple
        chips
        hide-selected
        deletable-chips
        return-object
        clearable
      ></v-autocomplete>
</template>

<style>
</style>

<script>
import { mapGetters } from 'vuex';
import debounce from 'debounce';

export default {
  name: 'roommate-field',
  props: {
    value: {
      type: Array,
      default: () => [],
    },
    label: {
      type: String,
      default: 'People',
    },
    placeholder: {
      type: String,
      default: 'Start Typing to Search',
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  data: () => ({
    roommates: null,
    options: [],
    optionsLoading: false,
    search: '',
    departments: {},
  }),
  computed: {
    ...mapGetters([
      'event',
    ]),
  },
  mounted() {
    this.roommates = this.value;
    const self = this;
    if (this.event.id) {
      this.post('/api/hotels/department_names', { event: this.event.id }).then((res) => {
        if (res.success) {
          self.departments = res.departments;
        }
      });
    }
  },
  methods: {
    makeSearch: (value, self) => {
      if (!value) {
        self.options = [];
      }
      if (self.optionsLoading) {
        return;
      }
      self.optionsLoading = true;
      self.post('/api/hotels/roommate_search', {
        event: self.event.id,
        search: value,
      }).then((resp) => {
        if (resp.success) {
          resp.results.forEach((el) => {
            for (let i = 0; i < el.departments.length; i += 1) {
              if (Object.prototype.hasOwnProperty.call(self.departments, el.departments[i])) {
                el.departments[i] = self.departments[el.departments[i]].name;
              }
            }
            if (el.departments.length === 0) {
              el.text = el.name;
            } else {
              el.text = `${el.name} (${el.departments.join(', ')})`;
            }
          });
          resp.results.push(...self.roommates);
          self.options = resp.results;
          self.optionsLoading = false;
        }
      });
      self.optionsLoading = false;
    },
  },
  watch: {
    search(value) {
      if (!value) {
        return;
      }
      debounce(this.makeSearch, 200)(value, this);
    },
    roommates(value) {
      this.search = '';
      this.$emit('input', value);
    },
    event() {
      const self = this;
      this.post('/api/hotels/department_names', { event: this.event.id }).then((res) => {
        if (res.success) {
          self.departments = res.departments;
        }
      });
    },
  },
};
</script>
