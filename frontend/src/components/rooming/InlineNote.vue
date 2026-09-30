<template>
  <div class="inline-note" :class="{ compact }">
    <template v-if="!editing">
      <span v-if="modelValue" class="note-text" role="button" tabindex="0"
            :title="'Click to edit the ' + label" @click="start" @keydown.enter.prevent="start">
        {{ modelValue }}
      </span>
      <button v-else type="button" class="note-add" :title="'Add an ' + label" @click="start">
        <i class="pi pi-pencil" /> {{ placeholder }}
      </button>
    </template>
    <template v-else>
      <Textarea ref="input" v-model="draft" :autoResize="true" rows="2" class="w-full note-input"
                :placeholder="placeholder" @keydown.esc.prevent="cancel"
                @keydown.enter.ctrl.exact.prevent="commit" @keydown.enter.meta.exact.prevent="commit" />
      <div class="note-actions">
        <Button icon="pi pi-check" class="p-button-sm p-button-text" :loading="saving"
                title="Save (Ctrl+Enter)" @click="commit" />
        <Button icon="pi pi-times" class="p-button-sm p-button-text p-button-secondary"
                :disabled="saving" title="Cancel (Esc)" @click="cancel" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.inline-note {
  min-width: 8rem;
}
.note-text {
  display: inline-block;
  white-space: pre-wrap;
  cursor: text;
  border-bottom: 1px dashed var(--surface-border, #dee2e6);
  padding-bottom: 1px;
}
.note-text:hover,
.note-text:focus {
  border-bottom-color: var(--primary-color, #2196f3);
  outline: none;
}
.note-add {
  background: none;
  border: none;
  padding: 0;
  font: inherit;
  color: var(--text-color-secondary, #6c757d);
  cursor: pointer;
}
.note-add:hover {
  color: var(--primary-color, #2196f3);
}
.note-input {
  font-size: 0.9rem;
}
.note-actions {
  display: flex;
  justify-content: flex-end;
}
.compact .note-text,
.compact .note-add {
  font-size: 0.85rem;
}
</style>

<script>
// Click-to-edit text used for the admin-only notes on requests and rooms.
// The parent supplies `save(text)`; the value is only committed once that
// resolves, so a failed save leaves the old text in place.
export default {
  name: 'InlineNote',
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    save: {
      type: Function,
      required: true
    },
    label: {
      type: String,
      default: 'admin note'
    },
    placeholder: {
      type: String,
      default: 'Add admin note'
    },
    compact: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  data: () => ({
    editing: false,
    draft: '',
    saving: false
  }),
  methods: {
    start () {
      this.draft = this.modelValue || ''
      this.editing = true
      this.$nextTick(() => {
        const input = this.$refs.input && this.$refs.input.$el
        if (input) {
          input.focus()
        }
      })
    },
    cancel () {
      if (!this.saving) {
        this.editing = false
      }
    },
    async commit () {
      const text = this.draft.trim()
      if (text === (this.modelValue || '')) {
        this.editing = false
        return
      }
      this.saving = true
      try {
        await this.save(text)
        this.$emit('update:modelValue', text)
        this.editing = false
      } catch (e) {
        this.$toast.add({ severity: 'error', summary: 'Could not save the ' + this.label, life: 3000 })
      }
      this.saving = false
    }
  }
}
</script>
