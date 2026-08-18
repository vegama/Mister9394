<script setup>
import { computed } from 'vue'
const props=defineProps({focus:{type:Object,default:null},viewLabel:{type:String,default:''}})
const emit=defineEmits(['back','home','clear'])
const meta=computed(()=>[props.focus?.owner,props.focus?.status,props.viewLabel].filter(Boolean).join(' · '))
</script>
<template>
  <aside v-if="focus" class="f-decision-focus" aria-label="Asunto que estás resolviendo">
    <div class="f-decision-focus__copy">
      <span class="f-ui-eyebrow">Estás resolviendo</span>
      <strong>{{focus.title || 'Asunto pendiente'}}</strong>
      <p>{{focus.detail || 'Has llegado aquí desde una decisión del centro de mando.'}}</p>
      <p v-if="focus.next_step"><b>Siguiente:</b> {{focus.next_step}}</p>
      <p v-if="focus.consequence"><b>Si esperas:</b> {{focus.consequence}}</p>
      <small v-if="meta">{{meta}}</small>
    </div>
    <div class="f-decision-focus__actions">
      <button type="button" class="football-button" @click="emit('home')">Ver pendientes</button>
      <button type="button" class="football-button" @click="emit('back')">← Volver al origen</button>
      <button type="button" class="focus-clear" aria-label="Cerrar contexto" title="Cerrar contexto" @click="emit('clear')">×</button>
    </div>
  </aside>
</template>
