<script setup>
import { computed, nextTick, ref, watch } from 'vue'
const props=defineProps({open:{type:Boolean,default:false},groups:{type:Array,default:()=>[]},active:{type:String,default:'home'}})
const emit=defineEmits(['close','navigate'])
const query=ref('')
const input=ref(null)
const palette=ref(null)
const activeIndex=ref(0)
let focusBeforeOpen=null
const rows=computed(()=>props.groups.flatMap(group=>group.items.map(item=>({...item,group:group.label}))))
const filtered=computed(()=>{
  const needle=query.value.trim().toLocaleLowerCase('es')
  if(!needle)return rows.value
  return rows.value.filter(row=>`${row.label} ${row.group}`.toLocaleLowerCase('es').includes(needle))
})
watch(()=>props.open,async value=>{
 if(value){
  focusBeforeOpen=document.activeElement instanceof HTMLElement?document.activeElement:null
  query.value='';activeIndex.value=0;await nextTick();input.value?.focus()
 }else{
  await nextTick();focusBeforeOpen?.focus?.();focusBeforeOpen=null
 }
})
watch(query,()=>{activeIndex.value=0})
watch(filtered,rows=>{if(!rows.length)activeIndex.value=0;else if(activeIndex.value>=rows.length)activeIndex.value=rows.length-1})
function choose(id){emit('navigate',id);emit('close')}
function move(delta){
 if(!filtered.value.length)return
 activeIndex.value=(activeIndex.value+delta+filtered.value.length)%filtered.value.length
 nextTick(()=>document.querySelector('.command-results button.keyboard-active')?.scrollIntoView({block:'nearest'}))
}
function focusableNodes(){
 return [...(palette.value?.querySelectorAll('button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])')||[])]
}
function trapTab(event){
 const nodes=focusableNodes()
 if(!nodes.length)return
 const first=nodes[0],last=nodes[nodes.length-1]
 if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}
 else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}
}
function handleKey(event){
 if(event.key==='Tab'){trapTab(event);return}
 if(event.key==='ArrowDown'){event.preventDefault();move(1);return}
 if(event.key==='ArrowUp'){event.preventDefault();move(-1);return}
 if(event.key==='Enter'&&filtered.value[activeIndex.value]){event.preventDefault();choose(filtered.value[activeIndex.value].id)}
}
</script>
<template>
  <div v-if="open" class="command-palette-backdrop" @mousedown.self="emit('close')" @keydown.esc="emit('close')" @keydown="handleKey">
    <section ref="palette" class="command-palette" role="dialog" aria-modal="true" aria-label="Ir a una sección">
      <header><span><small>ACCESO RÁPIDO</small><strong>Ir a…</strong></span><button type="button" @click="emit('close')" aria-label="Cerrar">×</button></header>
      <label class="command-search"><span class="sr-only">Buscar sección</span><input ref="input" v-model="query" type="search" placeholder="Plantilla, mercado, calendario…" aria-controls="manager-command-results" :aria-activedescendant="filtered[activeIndex]?`command-${filtered[activeIndex].id}`:undefined"></label>
      <div id="manager-command-results" class="command-results" role="listbox" aria-label="Secciones disponibles">
        <button v-for="(row,index) in filtered" :id="`command-${row.id}`" :key="row.id" type="button" role="option" :aria-selected="index===activeIndex" :class="{active:row.id===active,'keyboard-active':index===activeIndex}" @mouseenter="activeIndex=index" @click="choose(row.id)"><span><small>{{row.group}}</small><strong>{{row.label}}</strong></span><b>{{row.id===active?'Actual':'→'}}</b></button>
        <div v-if="!filtered.length" class="command-empty"><strong>No encuentro esa sección</strong><span>Prueba con el nombre que ves en el menú lateral.</span></div>
      </div>
      <footer><span>↑ ↓ para elegir · Enter para abrir</span><span>Esc para cerrar</span><span>Ctrl/⌘ + K desde cualquier pantalla</span></footer>
    </section>
  </div>
</template>
