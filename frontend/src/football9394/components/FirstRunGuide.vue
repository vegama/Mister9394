<script setup>
import { computed } from 'vue'
const props=defineProps({dashboard:{type:Object,default:()=>({})},selection:{type:Object,default:()=>({})},lineupDirty:{type:Boolean,default:false},nextMatch:{type:Object,default:null}})
const emit=defineEmits(['dismiss','navigate','open-decision','continue'])
const blocker=computed(()=>props.dashboard?.blocking_decisions?.[0]||props.dashboard?.pending_decisions?.[0]||null)
const selectionReady=computed(()=>Boolean(!props.lineupDirty&&props.selection?.valid&&(props.selection?.starter_ids||[]).length===11&&(props.selection?.bench_ids||[]).length===5))
const primary=computed(()=>{
 if(blocker.value)return {label:'Resolver prioridad',kind:'decision'}
 if(!selectionReady.value)return {label:'Preparar convocatoria',kind:'navigate',target:'squad'}
 if(props.nextMatch)return {label:'Revisar plan de partido',kind:'navigate',target:'tactics'}
 return {label:'Continuar la carrera',kind:'continue'}
})
function run(){
 if(primary.value.kind==='decision')emit('open-decision',blocker.value)
 else if(primary.value.kind==='navigate')emit('navigate',primary.value.target)
 else emit('continue')
}
</script>

<template>
<section class="first-run-guide" aria-label="Guía contextual del primer día">
  <div class="first-run-mark" aria-hidden="true">93</div>
  <div class="first-run-copy"><small>PRIMER DÍA · AYUDA CONTEXTUAL</small><strong>No necesitas revisar todos los menús antes de empezar.</strong><p>Míster se organiza alrededor de situaciones: resuelve lo que requiera atención, deja tu equipo preparado y usa <b>Continuar</b>. La carrera se detendrá cuando necesite una decisión importante.</p><div class="first-run-steps"><span :class="{ready:!blocker}"><b>1</b> Atiende la prioridad</span><span :class="{ready:selectionReady}"><b>2</b> Deja listo el 11 + 5</span><span><b>3</b> Observa las consecuencias</span></div></div>
  <div class="first-run-actions"><button type="button" class="football-button primary" @click="run">{{primary.label}}</button><button type="button" class="text-action" @click="emit('dismiss')">Ya sé cómo funciona</button><span>Ctrl/⌘ + K abre “Ir a…” en cualquier momento.</span></div>
</section>
</template>
