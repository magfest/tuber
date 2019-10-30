<template>
  <v-autocomplete
      v-model="roommates"
      :items="options"
      :loading="optionsLoading"
      :search-input.sync="search"
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
      auto-select-first
      return-object
      hide-no-data
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
    roommates: [],
    options: [],
    optionsLoading: false,
    search: '',
    initialized: false,
  }),
  computed: {
    ...mapGetters([
      'event',
    ]),
  },
  asyncComputed: {
    department_names() {
      const self = this;
      return new Promise((resolve) => {
        if (self.event.id) {
          self.post('/api/hotels/department_names', {
            event: self.event.id,
          }).then((res) => {
            if (res.success) {
              resolve(res.departments);
            }
            resolve({});
          });
        }
      });
    },
    roommates() {
      const resRoommates = [];
      const self = this;
      return new Promise((resolve) => {
        self.value.forEach((id) => {
          self.post('/api/hotels/roommate_lookup', {
            event: self.event.id,
            badge: id,
          }).then((res) => {
            if (res.success) {
              for (let i = 0; i < res.roommate.departments.length; i += 1) {
                if (Object.prototype.hasOwnProperty.call(self.department_names, res.roommate.departments[i])) {
                  res.roommate.departments[i] = self.department_names[res.roommate.departments[i]].name;
                }
              }
              if (res.roommate.departments.length === 0) {
                res.roommate.text = res.roommate.name;
              } else {
                res.roommate.text = `${res.roommate.name} (${res.roommate.departments.join(', ')})`;
              }
              resRoommates.push(res.roommate);
              if (self.value.length === resRoommates.length) {
                resolve(resRoommates);
              }
            } else {
              resolve([]);
            }
          });
        });
      });
    },
  },
  mounted() {
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
              if (Object.prototype.hasOwnProperty.call(self.department_names, el.departments[i])) {
                el.departments[i] = self.department_names[el.departments[i]].name;
              }
            }
            if (el.departments.length === 0) {
              el.text = el.name;
            } else {
              el.text = `${el.name} (${el.departments.join(', ')})`;
            }
          });
          if (self.roommates) {
            resp.results.push(...self.roommates);
          }
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
      this.options = value;
      const ret = [];
      for (let i = 0; i < value.length; i += 1) {
        ret.push(value[i].id);
        if (this.value[i] !== ret[i]) {
          this.$emit('input', ret);
        }
      }
    },
  },
};
</script>
