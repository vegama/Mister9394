<script setup>
import { computed } from 'vue'
const props=defineProps({
  steps:{type:Array,default:()=>[]},
  activeStep:{type:String,default:''},
  compact:{type:Boolean,default:false},
  ariaLabel:{type:String,default:'Progreso del proceso'},
})
const rows=computed(()=>{
  const activeIndex=props.steps.findIndex(step=>String(step.id??step.key)===String(props.activeStep))
  return props.steps.map((step,index)=>({
    ...step,
    id:String(step.id??step.key??index),
    number:index+1,
    active:String(step.id??step.key)===String(props.activeStep) || step.active===true,
    done:step.done===true || ['done','clear','completed','complete'].includes(String(step.state||'').toLowerCase()) || (step.done==null&&activeIndex>=0&&index<activeIndex),
  }))
})
</script>

<template>
  <ol class="f-ui-process-trail" :class="{'is-compact':compact}" :aria-label="ariaLabel">
    <li v-for="step in rows" :key="step.id" :class="{'is-active':step.active,'is-done':step.done}" :aria-current="step.active?'step':undefined">
      <span class="f-ui-process-trail__marker" aria-hidden="true">{{step.done?'✓':step.number}}</span>
      <span class="f-ui-process-trail__copy"><strong>{{step.label}}</strong><small v-if="step.detail">{{step.detail}}</small></span>
      <span v-if="step.owner" class="f-ui-process-trail__owner">{{step.owner}}</span>
    </li>
  </ol>
</template>
