<script setup>
import UiPageHeader from '../../components/ui/UiPageHeader.vue'
import UiEmptyState from '../../components/ui/UiEmptyState.vue'
defineProps({categories:{type:Array,default:()=>[]},category:{type:String,default:'Todas'},news:{type:Array,default:()=>[]},managerWorld:{type:Object,default:()=>({history:[],pressure:{},unemployed_count:0})},informationWorld:{type:Object,default:()=>({threads:[],media_reputation:{}})},formatDate:{type:Function,required:true}})
const emit=defineEmits(['update:category','open-entity'])
function actionsFor(item){
 const entity=item?.entity||{}
 const actions=[]
 if(entity.player_id)actions.push({type:'player',id:entity.player_id,label:'Ver jugador'})
 if(entity.team_id)actions.push({type:'team',id:entity.team_id,label:'Ver club'})
 if(entity.opponent_id)actions.push({type:'team',id:entity.opponent_id,label:'Ver rival'})
 if(entity.competition_id)actions.push({type:'competition',id:entity.competition_id,kind:entity.competition_kind||'league',label:'Ver competición'})
 return actions
}
</script>
<template>
<section class="screen-grid news-screen modern-r7">
  <article class="football-panel news-archive"><UiPageHeader eyebrow="MEMORIA VIVA" title="Noticias" description="La hemeroteca convierte hechos reales de tu partida en contexto: qué pasó, a quién afecta y por qué vuelve a importar." :status="`${news.length} noticia${news.length===1?'':'s'}`" />
    <nav class="chip-filter"><button v-for="cat in categories" :key="cat" type="button" :class="{active:category===cat}" @click="emit('update:category',cat)">{{cat}}</button></nav>
    <div class="news-stream"><article v-for="n in news" :key="n.id" class="story-card modern-story" :class="`importance-${n.importance}`"><time>{{formatDate(n.date)}}</time><div><small>{{n.category}}</small><h3>{{n.headline}}</h3><p>{{n.detail}}</p><div v-if="actionsFor(n).length" class="story-actions"><button v-for="action in actionsFor(n)" :key="`${action.type}-${action.id}`" type="button" class="text-action" @click="emit('open-entity',action)">{{action.label}} →</button></div></div></article><UiEmptyState v-if="!news.length" title="Todavía no hay hechos suficientes para abrir la hemeroteca" detail="La portada se alimenta de resultados, fichajes, lesiones, contratos, selecciones y cambios de carrera que hayan ocurrido realmente." hint="Continúa la partida: cuando un hecho tenga contexto suficiente aparecerá aquí sin generar noticias de relleno." /></div>
  </article>
  <aside class="side-stack news-world-rail">
    <article class="football-panel editorial-note"><span class="editorial-mark">93</span><h2>Una partida, una historia</h2><p>Resultados, fichajes, lesiones, contratos, selecciones y transiciones de temporada alimentan esta portada. No hay noticias de relleno.</p></article>
    <article class="football-panel"><small>ORIGEN</small><h2>De dónde salen las historias</h2><div class="manager-change-list"><article v-for="thread in (informationWorld.threads||[]).slice(0,5)" :key="thread.id"><time>{{formatDate(thread.date)}} · {{thread.stage}}</time><strong>{{thread.news?.headline || thread.rumour?.text || thread.fact?.kind}}</strong><span>{{thread.rumour ? `Rumor ${thread.certainty}%` : 'Hecho registrado'}}<template v-if="thread.reactions?.length"> · {{thread.reactions.length}} reacción{{thread.reactions.length===1?'':'es'}}</template><template v-if="thread.consequences?.length"> · {{thread.consequences.length}} consecuencia{{thread.consequences.length===1?'':'s'}}</template></span></article><p v-if="!informationWorld.threads?.length" class="rail-empty">Aún no hay una cadena causal que mostrar.</p></div></article>
    <article class="football-panel manager-carousel"><small>MUNDO TÉCNICO</small><h2>Mercado de banquillos</h2><p>{{managerWorld.unemployed_count||0}} entrenadores de la partida están actualmente libres.</p><div class="manager-change-list"><article v-for="m in [...(managerWorld.history||[])].reverse().slice(0,4)" :key="`${m.date}-${m.team_id}-${m.to_manager_id}`"><time>{{formatDate(m.date)}}</time><strong>{{m.team_name || `Club ${m.team_id}`}}</strong><span>{{m.from_manager_name || 'Anterior técnico'}} → {{m.to_manager_name || `Entrenador ${m.to_manager_id}`}}</span><em v-if="m.position">{{m.position}}º · expectativa {{m.expected_position}}º</em></article><p v-if="!managerWorld.history?.length" class="rail-empty">Los banquillos todavía conservan sus técnicos iniciales.</p></div></article>
  </aside>
</section>
</template>