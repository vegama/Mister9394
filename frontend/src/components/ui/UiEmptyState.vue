<script setup>
defineProps({
  title:{type:String,default:'Nada que mostrar'},
  description:{type:String,default:''},
  hint:{type:String,default:''},
  icon:{type:String,default:'—'},
  compact:{type:Boolean,default:false},
})
</script>
<template>
  <div class="f-ui-empty-state" :class="{'is-compact':compact}" role="status">
    <span v-if="icon" class="f-ui-empty-state__icon" aria-hidden="true">{{icon}}</span>
    <div class="f-ui-empty-state__copy"><strong>{{title}}</strong><span v-if="description">{{description}}</span><small v-if="hint">{{hint}}</small></div>
    <div v-if="$slots.default" class="f-ui-empty-state__actions"><slot /></div>
  </div>
</template>
