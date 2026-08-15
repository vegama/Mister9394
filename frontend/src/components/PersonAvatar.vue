<script setup>
import { computed, ref, watch } from 'vue'
import FootballKitAvatar from './FootballKitAvatar.vue'

const props = defineProps({
  person: { type: Object, default: null },
  teamColors: { type: Object, default: null },
  shirtNumber: { type: [String, Number], default: null },
  size: { type: Number, default: 60 },
  height: { type: Number, default: null },
  decorative: { type: Boolean, default: false },
  variant: { type: String, default: 'auto' },
})

const imageFailed = ref(false)
watch(() => [props.person?.photo_path, props.person?.photo_url], () => { imageFailed.value = false })
const photo = computed(() => imageFailed.value ? null : (props.person?.photo_path || props.person?.photo_url || null))
const imageHeight = computed(() => props.height ?? props.size)
const name = computed(() => props.person?.display_name || props.person?.name || props.person?.full_name || '')
const alt = computed(() => props.decorative ? '' : (name.value ? `Foto de ${name.value}` : ''))
const isPlayer = computed(() => props.variant === 'player' || (props.variant === 'auto' && (!!props.person?.positions || props.shirtNumber != null)))
const initials = computed(() => name.value.split(/\s+/).filter(Boolean).slice(0,2).map(row => row[0]).join('').toUpperCase() || '•')
const SAFE = /^#(?:[0-9a-f]{3}|[0-9a-f]{6})$/i
const safeColor = (value, fallback) => SAFE.test(String(value || '')) ? value : fallback
const primary = computed(() => safeColor(props.teamColors?.primary, '#24475c'))
const secondary = computed(() => safeColor(props.teamColors?.secondary, '#f2c339'))
</script>

<template>
  <img v-if="photo" :src="photo" :width="size" :height="imageHeight" class="photo-avatar"
       :alt="alt" loading="lazy" @error="imageFailed = true">
  <FootballKitAvatar v-else-if="isPlayer" :size="size" :number="shirtNumber ?? person?.shirt_number" :name="name"
                     :colors="{primary,secondary}" :alt="alt" :decorative="decorative" />
  <svg v-else :width="size" :height="size" viewBox="0 0 64 64" class="person-fallback-avatar"
       role="img" :aria-label="alt || undefined" :aria-hidden="alt ? undefined : 'true'">
    <title v-if="alt">{{ alt }}</title>
    <circle cx="32" cy="32" r="30" fill="#172638" stroke="#60758a" stroke-width="2"/>
    <circle cx="32" cy="23" r="10" fill="#8293a4"/>
    <path d="M13 55c2-13 10-20 19-20s17 7 19 20" fill="#8293a4"/>
    <text x="32" y="59" text-anchor="middle" font-size="8" font-weight="900" fill="#f5f7fa">{{ initials }}</text>
  </svg>
</template>
