<template>
     <v-card :loading="loading">
        <v-card-title class="headline grey lighten-2" primary-title>
            Edit Email
        </v-card-title>
        <br>
        <v-card-text>
            <v-form>
                <v-text-field outlined label="Name" v-model="value.name"></v-text-field>
                <v-text-field outlined label="Description" v-model="value.description"></v-text-field>
                <p>Send filter (lua)</p>
                <editor v-model="value.code" lang="lua" width="650" height="200"></editor><br>
                <v-text-field outlined label="Subject" v-model="value.subject"></v-text-field>
                <v-textarea outlined label="Body" v-model="value.body"></v-textarea>
                <v-checkbox outlined v-model="value.active" label="Active"></v-checkbox>
                <v-checkbox outlined v-model="value.send_once" label="Only send once"></v-checkbox>
                <v-select outlined label="Email Source" v-model="value.source" :items="sources" item-text="display" item-value="id"></v-select>
            </v-form>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn left @click="$emit('input')">Close</v-btn>
            <v-btn color="primary" text @click="save_data">Save</v-btn>
        </v-card-actions>
    </v-card>
</template>

<script>
import editor from 'vue2-ace-editor';
import { mapAsyncDump } from '../../mixins/rest';
import 'brace/ext/language_tools';
import 'brace/mode/lua';
import 'brace/theme/chrome';

export default {
  name: 'email-form',
  components: {
    editor,
  },
  data: () => ({
    loading: false,
  }),
  props: {
    value: {
      default: () => ({
        name: '',
        description: '',
        code: '',
        subject: '',
        body: '',
        active: false,
        send_once: true,
        source: 0,
      }),
    },
  },
  computed: {
    sources() {
      const result = [];
      this.email_sources.forEach((emailSource) => {
        emailSource.display = `${emailSource.address} (${emailSource.name})`;
        result.push(emailSource);
      });
      return result;
    },
  },
  asyncComputed: {
    ...mapAsyncDump(['email_sources']),
  },
  methods: {
    save_data() {
      this.loading = true;
      this.save('emails', this.value).then(() => {
        this.loading = false;
        this.$emit('saved');
        this.$emit('input');
      }).catch(() => {
        this.loading = false;
        this.notify('Failed to save email.');
      });
    },
  },
};
</script>
