<script setup>
defineProps({categories:{type:Array,default:()=>[]},category:{type:String,default:'Todas'},news:{type:Array,default:()=>[]},managerWorld:{type:Object,default:()=>({history:[],pressure:{},unemployed_count:0})},formatDate:{type:Function,required:true}})
const emit=defineEmits(['update:category'])
</script>
<template>
<section class="screen-grid news-screen modern-r7">
  <article class="football-panel news-archive"><header class="workspace-heading"><div><small>Memoria viva</small><h2>Noticias</h2><p>La hemeroteca sólo recoge hechos ocurridos realmente en esta partida.</p></div></header>
    <nav class="chip-filter"><button v-for="cat in categories" :key="cat" type="button" :class="{active:category===cat}" @click="emit('update:category',cat)">{{cat}}</button></nav>
    <div class="news-stream"><article v-for="n in news" :key="n.id" class="story-card modern-story" :class="`importance-${n.importance}`"><time>{{formatDate(n.date)}}</time><div><small>{{n.category}}</small><h3>{{n.headline}}</h3><p>{{n.detail}}</p></div></article><div v-if="!news.length" class="empty-football-state">Todavía no hay hechos suficientes para abrir la hemeroteca.</div></div>
  </article>
  <aside class="side-stack news-world-rail">
    <article class="football-panel editorial-note"><span class="editorial-mark">93</span><h2>Una partida, una historia</h2><p>Resultados, fichajes, lesiones, contratos, selecciones y transiciones de temporada alimentan esta portada. No hay noticias de relleno.</p></article>
    <article class="football-panel manager-carousel"><small>MUNDO TÉCNICO</small><h2>Mercado de banquillos</h2><p>{{managerWorld.unemployed_count||0}} entrenadores de la partida están actualmente libres.</p><div class="manager-change-list"><article v-for="m in [...(managerWorld.history||[])].reverse().slice(0,4)" :key="`${m.date}-${m.team_id}-${m.to_manager_id}`"><time>{{formatDate(m.date)}}</time><strong>{{m.team_name || `Club ${m.team_id}`}}</strong><span>{{m.from_manager_name || 'Anterior técnico'}} → {{m.to_manager_name || `Entrenador ${m.to_manager_id}`}}</span><em v-if="m.position">{{m.position}}º · expectativa {{m.expected_position}}º</em></article><p v-if="!managerWorld.history?.length" class="rail-empty">Los banquillos todavía conservan sus técnicos iniciales.</p></div></article>
  </aside>
</section>
</template>