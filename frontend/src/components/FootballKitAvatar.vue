<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: { type: Number, default: 60 },
  number: { type: [String, Number], default: null },
  name: { type: String, default: '' },
  colors: { type: Object, default: null },
  alt: { type: String, default: '' },
  decorative: { type: Boolean, default: false },
})

const SAFE = /^#(?:[0-9a-f]{3}|[0-9a-f]{6})$/i
const primary = computed(() => SAFE.test(String(props.colors?.primary || '')) ? props.colors.primary : '#1d6b44')
const secondary = computed(() => SAFE.test(String(props.colors?.secondary || '')) ? props.colors.secondary : '#f2f5f3')
const shownNumber = computed(() => props.number == null || props.number === '' ? '•' : String(props.number).slice(0, 2))
const aria = computed(() => props.decorative ? undefined : (props.alt || (props.name ? `Jugador ${props.name}` : 'Jugador')))
</script>

<template>
  <svg
    class="football-kit-avatar"
    :width="size" :height="size" viewBox="0 0 72 72"
    role="img" :aria-label="aria" :aria-hidden="decorative ? 'true' : undefined"
  >
    <title v-if="aria">{{ aria }}</title>
    <defs>
      <linearGradient id="fka-shirt" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0" :stop-color="primary"/>
        <stop offset="1" :stop-color="primary" stop-opacity=".72"/>
      </linearGradient>
    </defs>
    <circle cx="36" cy="36" r="34" fill="#0b1714" stroke="#38564a" stroke-width="2"/>
    <circle cx="36" cy="19" r="10" fill="#b78462"/>
    <path d="M28 17c2-8 15-10 18 0-3-3-6-5-10-5s-6 2-8 5z" fill="#1e1714"/>
    <path d="M15 61c1-17 8-27 21-27s20 10 21 27z" fill="url(#fka-shirt)" stroke="#07110e" stroke-width="1.5"/>
    <path d="M23 38l13 8 13-8" fill="none" :stroke="secondary" stroke-width="3" opacity=".9"/>
    <text x="36" y="59" text-anchor="middle" :fill="secondary" font-size="18" font-weight="900">{{ shownNumber }}</text>
  </svg>
</template>
