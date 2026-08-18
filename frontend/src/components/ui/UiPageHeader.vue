<script setup>
defineProps({
  eyebrow:{type:String,default:''},
  title:{type:String,required:true},
  description:{type:String,default:''},
  status:{type:String,default:''},
  tone:{type:String,default:'neutral'},
})
</script>

<template>
  <header class="f-ui-page-header" :class="`tone-${tone}`">
    <div class="f-ui-page-header__copy">
      <span v-if="eyebrow" class="f-ui-eyebrow">{{eyebrow}}</span>
      <h2>{{title}}</h2>
      <p v-if="description">{{description}}</p>
      <slot />
    </div>
    <div v-if="status || $slots.actions" class="f-ui-page-header__right">
      <span v-if="status" class="f-ui-page-header__status">{{status}}</span>
      <div v-if="$slots.actions" class="f-ui-page-header__actions"><slot name="actions" /></div>
    </div>
  </header>
</template>
