<template>
    <div class="variable-tree">
        <div v-for="node in nodes" :key="node.path || node.name">
            <div class="var-row" :style="{ paddingLeft: depth * 1.25 + 'rem' }">
                <button v-if="node.children && node.children.length" type="button" class="var-toggle"
                        :aria-label="(expanded[node.path] ? 'Collapse ' : 'Expand ') + node.path"
                        @click="toggle(node.path)">{{ expanded[node.path] ? '−' : '+' }}</button>
                <span v-else class="var-toggle-spacer"></span>
                <code class="var-name" :title="prefix + node.path">{{ prefix + node.path }}</code>
                <code v-if="'value' in node" class="var-value">{{ formatVar(node.value) }}</code>
            </div>
            <VariableTree v-if="expanded[node.path] && node.children" :nodes="node.children"
                          :prefix="prefix" :depth="depth + 1" />
        </div>
    </div>
</template>

<style scoped>
.var-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  padding: 0.15rem 0;
  border-bottom: 1px solid var(--surface-border, #dee2e6);
}
.var-toggle,
.var-toggle-spacer {
  flex: 0 0 1.25rem;
  width: 1.25rem;
}
.var-toggle {
  height: 1.25rem;
  padding: 0;
  border: 1px solid var(--surface-border, #dee2e6);
  border-radius: 3px;
  background: var(--surface-0, #fff);
  color: var(--text-color, #495057);
  font-family: monospace;
  line-height: 1;
  cursor: pointer;
}
.var-name {
  min-width: 11rem;
  font-weight: 600;
  word-break: break-all;
}
.var-value {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.85rem;
}
</style>

<script>
export default {
  name: 'VariableTree',
  props: {
    nodes: { type: Array, required: true },
    prefix: { type: String, default: '' },
    depth: { type: Number, default: 0 }
  },
  data () {
    return {
      expanded: {}
    }
  },
  methods: {
    toggle (path) {
      this.expanded[path] = !this.expanded[path]
    },
    formatVar (value) {
      if (value === null || value === undefined) {
        return 'nil'
      }
      if (typeof value === 'string') {
        return value
      }
      return JSON.stringify(value)
    }
  }
}
</script>
