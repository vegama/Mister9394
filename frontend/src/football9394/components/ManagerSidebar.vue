<script setup>
import ManagerNavIcon from './ManagerNavIcon.vue'
defineProps({
  groups: { type: Array, default: () => [] },
  active: { type: String, default: 'home' },
  club: { type: Object, default: () => ({}) },
  season: { type: String, default: '1993-94' },
  crestUrl: { type: String, default: '' },
})
const emit = defineEmits(['navigate', 'new-career'])
</script>

<template>
  <aside class="manager-sidebar" aria-label="Navegación principal">
    <div class="sidebar-brand">
      <div class="brand-mark" aria-hidden="true"><span></span><i></i></div>
      <div><strong>Míster</strong><small>93/94</small></div>
    </div>

    <div class="sidebar-club">
      <div class="sidebar-crest">
        <img v-if="crestUrl" :src="crestUrl" alt="" />
        <span v-else>{{ String(club?.name || 'FC').slice(0, 2).toUpperCase() }}</span>
      </div>
      <div class="sidebar-club-copy">
        <strong>{{ club?.name || 'Sin club' }}</strong>
        <span>{{ club?.league?.name || 'Sin competición' }}</span>
      </div>
    </div>

    <nav class="sidebar-nav">
      <section v-for="group in groups" :key="group.label" class="sidebar-nav-group">
        <small>{{ group.label }}</small>
        <button
          v-for="item in group.items"
          :key="item.id"
          type="button"
          class="sidebar-nav-item"
          :class="{ active: active === item.id }"
          :aria-current="active === item.id ? 'page' : undefined"
          @click="emit('navigate', item.id)"
        >
          <span class="sidebar-nav-icon"><ManagerNavIcon :name="item.id" /></span>
          <span>{{ item.label }}</span>
        </button>
      </section>
    </nav>

    <div class="sidebar-footer">
      <div><small>Temporada</small><strong>{{ season }}</strong></div>
      <button type="button" class="sidebar-career-button" @click="emit('new-career')">Nueva carrera</button>
    </div>
  </aside>
</template>
