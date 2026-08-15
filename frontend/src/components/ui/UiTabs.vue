<script setup>
import { nextTick, ref } from 'vue'
const props=defineProps({
  modelValue:{type:String,default:''},
  items:{type:Array,default:()=>[]},
  ariaLabel:{type:String,default:'Secciones'},
})
const emit=defineEmits(['update:modelValue','select'])
const buttons=ref([])
function choose(item){
  if(item?.disabled)return
  emit('update:modelValue',item.id)
  emit('select',item.id)
}
function enabledIndexes(){return props.items.map((item,index)=>item?.disabled?null:index).filter(index=>index!==null)}
async function focusAndChoose(index){
  const item=props.items[index]
  if(!item||item.disabled)return
  choose(item)
  await nextTick()
  buttons.value[index]?.focus()
}
function onKeydown(event,index){
  const enabled=enabledIndexes()
  if(!enabled.length)return
  const current=Math.max(0,enabled.indexOf(index))
  let target=null
  if(event.key==='ArrowRight'||event.key==='ArrowDown')target=enabled[(current+1)%enabled.length]
  else if(event.key==='ArrowLeft'||event.key==='ArrowUp')target=enabled[(current-1+enabled.length)%enabled.length]
  else if(event.key==='Home')target=enabled[0]
  else if(event.key==='End')target=enabled[enabled.length-1]
  if(target===null)return
  event.preventDefault()
  void focusAndChoose(target)
}
</script>

<template>
  <nav class="ui-tabs" role="tablist" :aria-label="ariaLabel">
    <button v-for="(item,index) in items" :key="item.id" :ref="el=>buttons[index]=el" type="button" role="tab" :class="{active:modelValue===item.id}" :disabled="item.disabled" :aria-selected="modelValue===item.id?'true':'false'" :tabindex="modelValue===item.id?0:-1" @click="choose(item)" @keydown="onKeydown($event,index)">
      <span>{{item.label}}</span><small v-if="item.badge!=null">{{item.badge}}</small>
    </button>
  </nav>
</template>
