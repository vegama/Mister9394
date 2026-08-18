<script setup>
defineProps({
  title: { type: String, default: 'Inicio' },
  date: { type: String, default: '' },
  matchday: { type: [String, Number], default: '—' },
  pendingCount: { type: Number, default: 0 },
  preseason: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
  version: { type: String, default: '' },
})
const emit = defineEmits(['advance'])
</script>

<template>
  <header class="manager-topbar">
    <div class="topbar-heading">
      <small>Míster 93/94 <span v-if="version" class="topbar-version">v{{ version }}</span></small>
      <h1>{{ title }}</h1>
    </div>
    <div class="topbar-meta">
      <div class="topbar-date"><span>{{ date }}</span><small>{{ preseason ? 'Pretemporada' : `Jornada ${matchday}` }}</small></div>
      <div v-if="pendingCount" class="attention-pill"><b>{{ pendingCount }}</b><span>{{ pendingCount === 1 ? 'decisión pendiente' : 'decisiones pendientes' }}</span></div>
      <button type="button" class="continue-button" :disabled="busy" :aria-busy="busy" @click="emit('advance')">
        <span>{{ busy ? 'Avanzando…' : 'Continuar' }}</span><i aria-hidden="true">{{ busy ? '···' : '→' }}</i>
      </button>
    </div>
  </header>
</template>
