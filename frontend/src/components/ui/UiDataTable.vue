<script setup>
defineProps({caption:{type:String,default:''},compact:{type:Boolean,default:false},sticky:{type:Boolean,default:true},stickyFirstColumn:{type:Boolean,default:false},ariaLabel:{type:String,default:''}})
</script>
<template>
  <div class="f-ui-data-table" :class="{'is-compact':compact,'is-sticky':sticky,'has-sticky-first':stickyFirstColumn}" role="region" :aria-label="ariaLabel||caption||'Tabla de datos'" tabindex="0">
    <table><caption v-if="caption">{{caption}}</caption><slot /></table>
  </div>
</template>
