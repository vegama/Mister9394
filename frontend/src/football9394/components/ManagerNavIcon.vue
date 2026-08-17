<script setup>
defineProps({ name: { type: String, required: true } })
</script>

<template>
  <svg class="manager-nav-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <template v-if="name==='home'"><path d="M3.5 10.5 12 3l8.5 7.5"/><path d="M5.5 9.5V21h13V9.5"/><path d="M9.5 21v-6h5v6"/></template>
    <template v-else-if="name==='squad'"><circle cx="9" cy="8" r="3"/><path d="M3.5 20c.4-4 2.3-6 5.5-6s5.1 2 5.5 6"/><circle cx="17" cy="9" r="2.3"/><path d="M15.5 14.5c3.2-.4 5 1.4 5.3 4.5"/></template>
    <template v-else-if="name==='tactics'"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16"/><circle cx="12" cy="12" r="2.5"/><path d="M3 9h4v6H3M21 9h-4v6h4"/></template>
    <template v-else-if="name==='market'"><circle cx="10" cy="10" r="5.5"/><path d="m14.2 14.2 5 5"/><path d="M8 10h4M10 8v4"/></template>
    <template v-else-if="name==='competitions'"><path d="M8 4h8v4c0 3-1.5 5-4 5s-4-2-4-5V4Z"/><path d="M8 6H4c0 3 1.4 5 4.4 5M16 6h4c0 3-1.4 5-4.4 5M12 13v4M8 20h8M9 17h6"/></template>
    <template v-else-if="name==='calendar'"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 10h18"/><path d="M7 14h3M14 14h3M7 18h3"/></template>
    <template v-else-if="name==='news'"><path d="M5 4h13a2 2 0 0 1 2 2v14H6a2 2 0 0 1-2-2V5a1 1 0 0 1 1-1Z"/><path d="M8 8h8M8 12h8M8 16h5"/></template>
    <template v-else-if="name==='club'"><path d="M12 3 20 6v5c0 5-3.2 8.4-8 10-4.8-1.6-8-5-8-10V6l8-3Z"/><path d="M9 10h6M12 7v6"/></template>
    <template v-else-if="name==='economy'"><rect x="3" y="6" width="18" height="14" rx="2"/><path d="M3 10h18M16 15h2"/><path d="M6 6V4h11"/></template>
    <template v-else-if="name==='national'"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.4 2.5 3.5 5.5 3.5 9S14.4 18.5 12 21c-2.4-2.5-3.5-5.5-3.5-9S9.6 5.5 12 3Z"/></template>
    <template v-else-if="name==='history'"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2M5.7 5.7 3.5 8"/></template>
    <template v-else><circle cx="12" cy="12" r="7"/></template>
  </svg>
</template>
