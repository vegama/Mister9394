<script setup>
defineProps({
  eyebrow:{type:String,default:'Tu decisión ahora'},
  title:{type:String,default:''},
  detail:{type:String,default:''},
  status:{type:String,default:''},
  tone:{type:String,default:'accent'},
  sticky:{type:Boolean,default:false},
})
</script>

<template>
  <section class="f-ui-action-dock" :class="[`tone-${tone}`,{'is-sticky':sticky}]" aria-label="Acción principal de la pantalla">
    <div class="f-ui-action-dock__copy">
      <span class="f-ui-eyebrow">{{eyebrow}}</span>
      <strong v-if="title">{{title}}</strong>
      <small v-if="detail">{{detail}}</small>
    </div>
    <div class="f-ui-action-dock__actions"><slot /></div>
    <span v-if="status" class="f-ui-action-dock__status" role="status" aria-live="polite">{{status}}</span>
  </section>
</template>
