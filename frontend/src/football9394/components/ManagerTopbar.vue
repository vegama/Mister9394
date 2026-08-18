<script setup>
defineProps({
  title: { type: String, default: 'Inicio' },
  context: { type: String, default: 'Centro de mando' },
  date: { type: String, default: '' },
  matchday: { type: [String, Number], default: '—' },
  pendingCount: { type: Number, default: 0 },
  preseason: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
  version: { type: String, default: '' },
  continueStatus: { type: Object, default: () => ({state:'ready',label:'Continuar',detail:'',action:'home'}) },
  canGoBack: { type: Boolean, default: false },
})
const emit = defineEmits(['advance','search','back'])
</script>

<template>
  <header class="manager-topbar">
    <div class="topbar-heading-row">
      <button v-if="canGoBack" type="button" class="topbar-back" aria-label="Volver al contexto anterior" title="Volver" @click="emit('back')">←</button>
      <div class="topbar-heading">
        <small>{{context}} <span v-if="version" class="topbar-version">· v{{ version }}</span></small>
        <h1>{{ title }}</h1>
      </div>
    </div>
    <div class="topbar-meta">
      <button type="button" class="topbar-search" aria-label="Ir rápidamente a una sección" title="Ir a una sección · Ctrl/⌘ + K" @click="emit('search')"><b aria-hidden="true">⌕</b><span>Ir a…</span><kbd>Ctrl K</kbd></button>
      <div class="topbar-date"><span>{{ date }}</span><small>{{ preseason ? 'Pretemporada' : `Jornada ${matchday}` }}</small></div>
      <div v-if="pendingCount" class="attention-pill" role="status"><b>{{ pendingCount }}</b><span>{{ pendingCount === 1 ? 'decisión pendiente' : 'decisiones pendientes' }}</span></div>
      <button type="button" class="continue-button" :class="`state-${continueStatus?.state || 'ready'}`" :disabled="busy" :aria-busy="busy" :title="continueStatus?.detail || 'Avanzar hasta el siguiente evento relevante'" @click="emit('advance')">
        <span>{{ busy ? 'Avanzando…' : (continueStatus?.label || 'Continuar') }}</span><i aria-hidden="true">{{ busy ? '···' : (continueStatus?.state==='blocked'?'!':'→') }}</i>
      </button>
    </div>
  </header>
</template>
