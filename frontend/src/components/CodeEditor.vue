<template>
  <div class="code-editor" :style="{ height: height }">
    <!-- The highlighted copy sits behind a transparent-text textarea, so the
         user edits a real textarea while seeing Prism's colors. -->
    <pre class="ce-highlight" ref="highlight" aria-hidden="true"><code v-html="highlighted"></code></pre>
    <textarea class="ce-input" ref="input" :value="modelValue || ''" spellcheck="false"
              autocapitalize="off" autocomplete="off" autocorrect="off" wrap="soft"
              :placeholder="placeholder"
              @input="$emit('update:modelValue', $event.target.value)"
              @scroll="syncScroll"></textarea>
  </div>
</template>

<style scoped>
.code-editor {
  position: relative;
  border: 1px solid var(--surface-border, #3f3f46);
  border-radius: 4px;
  /* Self-contained dark palette (One Dark-ish): the overlay <code> carries no
     language-* class, so the globally loaded Prism theme does not style it —
     without explicit colors the text inherits the app color and can vanish
     against the editor background. */
  background: #282c34;
  overflow: hidden;
  width: 100%;
}
.ce-highlight code {
  color: #abb2bf;
}
/* The globally loaded Prism theme (prism-coy) puts translucent backgrounds
   and shadows on some tokens; inside the editor only our palette applies. */
.ce-highlight :deep(.token) {
  background: transparent;
  text-shadow: none;
  border-radius: 0;
}
.ce-highlight :deep(.token.comment) {
  color: #7f848e;
  font-style: italic;
}
.ce-highlight :deep(.token.keyword) {
  color: #c678dd;
}
.ce-highlight :deep(.token.string) {
  color: #98c379;
}
.ce-highlight :deep(.token.number),
.ce-highlight :deep(.token.boolean),
.ce-highlight :deep(.token.nil) {
  color: #d19a66;
}
.ce-highlight :deep(.token.function) {
  color: #61afef;
}
.ce-highlight :deep(.token.operator) {
  color: #56b6c2;
}
.ce-highlight :deep(.token.punctuation) {
  color: #889099;
}
.ce-highlight :deep(.token.property),
.ce-highlight :deep(.token.variable) {
  color: #e06c75;
}
.ce-highlight :deep(.token.tag),
.ce-highlight :deep(.token.delimiter) {
  color: #e5c07b;
}
.ce-highlight, .ce-input {
  position: absolute;
  inset: 0;
  margin: 0;
  padding: 0.5rem 0.75rem;
  border: none;
  font-family: monospace;
  font-size: 0.9rem;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: break-word;
  tab-size: 4;
}
.ce-highlight {
  overflow: hidden;
  pointer-events: none;
  background: transparent;
}
.ce-highlight code {
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
  white-space: inherit;
  word-break: inherit;
  background: transparent;
  padding: 0;
}
.ce-input {
  width: 100%;
  height: 100%;
  resize: none;
  color: transparent;
  caret-color: #e6e6e6;
  background: transparent;
  overflow: auto;
  outline: none;
}
.ce-input::placeholder {
  color: #6b7280;
}
</style>

<script>
import Prism from 'prismjs'
import 'prismjs/components/prism-lua'
import 'prismjs/components/prism-markup-templating'
import 'prismjs/components/prism-django'

export default {
  name: 'CodeEditor',
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    // Any Prism grammar name; "lua" and "django" (Jinja) are preloaded.
    language: {
      type: String,
      default: 'django'
    },
    rows: {
      type: Number,
      default: 10
    },
    placeholder: {
      type: String,
      default: ''
    }
  },
  emits: [
    'update:modelValue'
  ],
  computed: {
    height () {
      return 'calc(' + this.rows * 1.4 + 'em + 1rem + 2px)'
    },
    highlighted () {
      // The trailing newline keeps an empty last line the same height as the
      // textarea's, so the caret never outruns the highlight layer.
      const code = (this.modelValue || '') + '\n'
      const grammar = Prism.languages[this.language]
      if (!grammar) {
        return code.replace(/&/g, '&amp;').replace(/</g, '&lt;')
      }
      return Prism.highlight(code, grammar, this.language)
    }
  },
  methods: {
    syncScroll () {
      this.$refs.highlight.scrollTop = this.$refs.input.scrollTop
      this.$refs.highlight.scrollLeft = this.$refs.input.scrollLeft
    }
  },
  watch: {
    modelValue () {
      this.$nextTick(this.syncScroll)
    }
  }
}
</script>
