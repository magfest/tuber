<template>
    <v-autocomplete
        v-model="roommates"
        :items="options"
        :loading="optionsLoading"
        :search-input.sync="search"
        hide-no-data
        item-text="name"
        item-value="id"
        :label="label"
        prepend-icon="person"
        append-icon=""
        :placeholder="placeholder"
        multiple
        chips
        hide-selected
        deletable-chips
        clearable
      ></v-autocomplete>
</template>

<style>
</style>

<script>
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
  },
  data: () => ({
    roommates: null,
    options: [],
    optionsLoading: false,
    search: '',
  }),
  mounted() {
    this.roommates = this.value;
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
      self.options = [
        {
          name: 'Mark Murnane (TechOps)',
          id: 0,
        },
        {
          name: 'Jason Spriggs (TechOps/Dispatch)',
          id: 1,
        },
      ];
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
  },
};
</script>
