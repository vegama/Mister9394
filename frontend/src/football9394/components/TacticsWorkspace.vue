<script setup>
import { computed } from 'vue'
import LineupPitch from './LineupPitch.vue'

const props = defineProps({
  formation: { type: String, default: '4-4-2' },
  mentality: { type: String, default: 'balanced' },
  tempo: { type: String, default: 'normal' },
  pressing: { type: String, default: 'medium' },
  directness: { type: String, default: 'mixed' },
  defensiveLine: { type: String, default: 'medium' },
  marking: { type: String, default: 'zonal' },
  width: { type: String, default: 'normal' },
  offsideTrap: { type: Boolean, default: false },
  identity: { type: Object, default: () => ({}) },
  players: { type: Array, default: () => [] },
  live: { type: Boolean, default: false },
  plan: { type: Object, default: () => ({build_up:'balanced',final_third:'mixed',transition:'balanced',familiarity:{},individual_instructions:[],opposition_instructions:[],set_piece_takers:{}}) },
  briefing: { type: Object, default: null },
})
const emit = defineEmits(['update:formation','update:mentality','update:tempo','update:pressing','update:directness','update:defensiveLine','update:marking','update:width','update:offsideTrap','save','apply-live','save-phase','set-player-instruction','set-opposition-instruction','set-piece-taker'])

const pct = value => { const n=Number(value||0); return `${n>0?'+':''}${Math.round(n*100)}%` }
const fitRows = computed(() => props.players.map(p => ({
  id:p.id, name:p.name || p.display_name, pos:p.pos || p.position,
  fit:Number(p.profile?.tactical_fit?.score ?? p.tactical_fit?.score ?? 0),
  fitLabel:p.profile?.tactical_fit?.label || p.tactical_fit?.label || 'Sin evaluar',
  role:p.profile?.identity?.archetype || p.identity?.archetype || 'Perfil',
})))
const averageFit = computed(() => {
  const values=fitRows.value.map(p=>p.fit).filter(v=>v>0)
  return values.length?Math.round(values.reduce((a,b)=>a+b,0)/values.length):null
})
const weakFits = computed(() => fitRows.value.filter(p=>p.fit>0 && p.fit<62).sort((a,b)=>a.fit-b.fit).slice(0,3))
const fitTone = value => value==null?'neutral':value>=78?'good':value>=62?'watch':'risk'
const instructionFor = id => (props.plan?.individual_instructions || []).find(row=>Number(row.player_id)===Number(id)) || {duty:'support',freedom:'balanced',pressing:'normal'}
function updateIndividual(player,key,value){
 const current=instructionFor(player.id)
 emit('set-player-instruction',{playerId:Number(player.id),instruction:{duty:current.duty||'support',freedom:current.freedom||'balanced',pressing:current.pressing||'normal',[key]:value}})
}
const oppositionFor = id => (props.plan?.opposition_instructions || []).find(row=>Number(row.player_id)===Number(id)) || {tight_mark:false,press:false,show_foot:'none'}
function updateOpposition(player,key,value){
 const current=oppositionFor(player.player_id)
 emit('set-opposition-instruction',{playerId:Number(player.player_id),instruction:{tight_mark:Boolean(current.tight_mark),press:Boolean(current.press),show_foot:current.show_foot||'none',[key]:value}})
}
</script>

<template>
  <section class="screen-grid tactics-screen redesigned-tactics">
    <article class="football-panel tactics-board-panel">
      <header class="panel-feature-head compact-head"><div><small>MODELO DE JUEGO</small><h2>{{ identity.formation_label || 'Plan de partido' }}</h2><p>El once y la estructura se leen de un vistazo antes de tocar una orden.</p></div></header>
      <div class="formation-switcher"><button v-for="f in ['4-4-2','4-3-3','4-2-3-1','4-5-1','4-4-1-1','4-3-1-2','4-2-4','3-5-2','3-4-3','3-4-1-2','5-3-2','5-4-1','5-2-3']" :key="f" type="button" :class="{active:formation===f}" @click="emit('update:formation',f)">{{f}}</button></div>
      <LineupPitch :formation="formation" :players="players" />
      <div class="tactical-score-strip"><span><small>Ataque</small><b>{{pct(identity.attack)}}</b></span><span><small>Posesión</small><b>{{pct(identity.possession)}}</b></span><span><small>Defensa</small><b>{{pct(identity.defence)}}</b></span><span><small>Riesgo</small><b>{{pct(identity.risk)}}</b></span></div>
      <div class="tactical-fit-panel d6-tactical-fit">
        <div class="tactical-fit-score" :class="fitTone(averageFit)"><small>ENCAJE DEL XI</small><b>{{averageFit ?? '—'}}</b><em v-if="averageFit!=null">/100</em></div>
        <div class="tactical-fit-copy"><strong>{{weakFits.length?'Hay piezas que fuerzan el plan':'El once acompaña el plan actual'}}</strong><span v-if="weakFits.length">{{weakFits.map(p=>`${p.name} (${p.fit})`).join(' · ')}}</span><span v-else>El sistema no detecta incompatibilidades fuertes entre el once guardado y la idea actual.</span></div>
      </div>
    </article>

    <article class="football-panel tactical-orders-panel">
      <header class="orders-title"><div><small>INSTRUCCIONES</small><h2>Órdenes del equipo</h2></div><span>1993-94</span></header>
      <div class="order-grid modern-orders">
        <label><span>Mentalidad</span><select :value="mentality" @change="emit('update:mentality',$event.target.value)"><option value="balanced">Equilibrada</option><option value="defensive">Defensiva</option><option value="attacking">Ofensiva</option></select><small>Cuánto riesgo acepta el equipo con balón.</small></label>
        <label><span>Ritmo</span><select :value="tempo" @change="emit('update:tempo',$event.target.value)"><option value="normal">Normal</option><option value="slow">Lento</option><option value="high">Alto</option></select><small>Velocidad de circulación y desgaste.</small></label>
        <label><span>Presión</span><select :value="pressing" @change="emit('update:pressing',$event.target.value)"><option value="medium">Media</option><option value="low">Baja</option><option value="high">Alta</option></select><small>Altura e intensidad sin balón.</small></label>
        <label><span>Pase</span><select :value="directness" @change="emit('update:directness',$event.target.value)"><option value="mixed">Mixto</option><option value="short">Corto</option><option value="direct">Directo</option></select><small>Cómo progresa el equipo hacia campo rival.</small></label>
        <label><span>Línea defensiva</span><select :value="defensiveLine" @change="emit('update:defensiveLine',$event.target.value)"><option value="medium">Media</option><option value="low">Baja</option><option value="high">Alta</option></select><small>Espacio que concedemos a la espalda.</small></label>
        <label><span>Anchura</span><select :value="width" @change="emit('update:width',$event.target.value)"><option value="normal">Normal</option><option value="narrow">Estrecha</option><option value="wide">Abierta</option></select><small>Ocupación horizontal del campo.</small></label>
        <label><span>Marcaje</span><select :value="marking" @change="emit('update:marking',$event.target.value)"><option value="zonal">Zonal</option><option value="man">Al hombre</option></select><small>Referencia defensiva principal.</small></label>
        <label class="switch-order"><span><b>Fuera de juego</b><small>Coordina una línea más agresiva.</small></span><input :checked="offsideTrap" type="checkbox" @change="emit('update:offsideTrap',$event.target.checked)"></label>
      </div>
      <div class="tactic-impact"><span><small>Carga de ritmo</small><b>{{pct(identity.tempo_load)}}</b></span><span><small>Presión</small><b>{{pct(identity.press_intensity)}}</b></span><span><small>Riesgo de línea</small><b>{{pct(identity.line_risk)}}</b></span><span><small>Amplitud ofensiva</small><b>{{pct(identity.width_attack)}}</b></span></div>
      <article class="phase-plan-layer nf4-phase-plan">
        <header><span><small>NF4 · COMPORTAMIENTO POR FASES</small><strong>Con balón, último tercio y transición</strong></span><b>{{plan.familiarity?.label || 'Asimilando'}} · {{plan.familiarity?.overall ?? '—'}}%</b></header>
        <div class="phase-plan-grid">
          <label><span>Salida</span><select :value="plan.build_up || 'balanced'" @change="emit('save-phase',{build_up:$event.target.value})"><option v-for="opt in plan.build_up_options || []" :key="opt.key" :value="opt.key">{{opt.label}}</option></select></label>
          <label><span>Último tercio</span><select :value="plan.final_third || 'mixed'" @change="emit('save-phase',{final_third:$event.target.value})"><option v-for="opt in plan.final_third_options || []" :key="opt.key" :value="opt.key">{{opt.label}}</option></select></label>
          <label><span>Tras recuperar</span><select :value="plan.transition || 'balanced'" @change="emit('save-phase',{transition:$event.target.value})"><option v-for="opt in plan.transition_options || []" :key="opt.key" :value="opt.key">{{opt.label}}</option></select></label>
        </div>
        <div class="familiarity-strip"><span v-for="key in ['shape','possession','pressing','set_pieces']" :key="key"><small>{{key==='shape'?'Estructura':key==='possession'?'Posesión':key==='pressing'?'Presión':'Balón parado'}}</small><b>{{plan.familiarity?.[key] ?? '—'}}%</b></span></div>
      </article>

      <article class="individual-orders-layer">
        <header><small>INSTRUCCIONES INDIVIDUALES</small><strong>Responsabilidades dentro del plan</strong></header>
        <div class="individual-order-row" v-for="p in players" :key="p.id">
          <span><b>{{p.name || p.display_name}}</b><small>{{p.pos || p.position}}</small></span>
          <select :value="instructionFor(p.id).duty" @change="updateIndividual(p,'duty',$event.target.value)"><option v-for="opt in plan.duty_options || []" :key="opt.key" :value="opt.key">{{opt.label}}</option></select>
          <select :value="instructionFor(p.id).freedom" @change="updateIndividual(p,'freedom',$event.target.value)"><option v-for="opt in plan.freedom_options || []" :key="opt.key" :value="opt.key">{{opt.label}}</option></select>
          <select :value="instructionFor(p.id).pressing" @change="updateIndividual(p,'pressing',$event.target.value)"><option v-for="opt in plan.player_press_options || []" :key="opt.key" :value="opt.key">{{opt.label}}</option></select>
        </div>
      </article>

      <article class="set-piece-layer">
        <header><small>BALÓN PARADO</small><strong>Lanzadores</strong></header>
        <div class="phase-plan-grid">
          <label v-for="kind in [{key:'corners',label:'Córners'},{key:'free_kicks',label:'Faltas'},{key:'penalties',label:'Penaltis'}]" :key="kind.key"><span>{{kind.label}}</span><select :value="plan.set_piece_takers?.[kind.key] || ''" @change="emit('set-piece-taker',{kind:kind.key,playerId:$event.target.value?Number($event.target.value):null})"><option value="">Automático</option><option v-for="p in players" :key="p.id" :value="p.id">{{p.name || p.display_name}}</option></select></label>
        </div>
      </article>

      <article v-if="briefing" class="opposition-layer">
        <header><span><small>PREPARACIÓN DEL RIVAL</small><strong>{{briefing.opponent?.team_name}}</strong></span><em>{{briefing.report?.assignee_name || 'Cuerpo técnico'}} · {{briefing.report?.quality_label || '—'}}</em></header>
        <p>{{briefing.recommendation}}</p>
        <div class="opposition-order-row" v-for="p in briefing.threats || []" :key="p.player_id">
          <span><b>{{p.name}}</b><small>{{p.position}} · {{p.identity}} · nivel {{p.level_range?.join('–')}}</small></span>
          <label><input type="checkbox" :checked="oppositionFor(p.player_id).tight_mark" @change="updateOpposition(p,'tight_mark',$event.target.checked)"> Marcaje estrecho</label>
          <label><input type="checkbox" :checked="oppositionFor(p.player_id).press" @change="updateOpposition(p,'press',$event.target.checked)"> Presionar</label>
          <select :value="oppositionFor(p.player_id).show_foot" @change="updateOpposition(p,'show_foot',$event.target.value)"><option value="none">Sin orientar</option><option value="left">Hacia izquierda</option><option value="right">Hacia derecha</option></select>
        </div>
      </article>

      <article class="tactical-people-layer">
        <header><small>QUIÉN EJECUTA EL PLAN</small><strong>El sistema depende de los futbolistas</strong></header>
        <div class="tactical-player-fit-list"><span v-for="p in fitRows" :key="p.id" :class="fitTone(p.fit)"><b>{{p.name}}</b><small>{{p.pos}} · {{p.role}}</small><em>{{p.fit?`${p.fit}/100`:'sin evaluar'}}</em></span></div>
      </article>
      <div class="tactics-footer"><p>La táctica modifica comportamientos y riesgos; un plan exigente sólo funciona si el once tiene perfiles compatibles para ejecutarlo.</p><div><button type="button" class="football-button primary" @click="emit('save')">Guardar táctica</button><button v-if="live" type="button" class="football-button" @click="emit('apply-live')">Aplicar en directo</button></div></div>
    </article>
  </section>
</template>

<style scoped>
.nf4-phase-plan,.individual-orders-layer,.set-piece-layer,.opposition-layer{margin-top:14px;padding:14px;border:1px solid var(--line,#d7dde6);border-radius:10px;background:var(--surface-soft,#f7f8fa)}.nf4-phase-plan header,.individual-orders-layer header,.set-piece-layer header,.opposition-layer header{display:flex;justify-content:space-between;gap:12px;margin-bottom:10px}.nf4-phase-plan header span,.individual-orders-layer header,.set-piece-layer header{display:grid}.nf4-phase-plan small,.individual-orders-layer small,.set-piece-layer small,.opposition-layer small{font-size:10px;color:var(--text-soft,#687386)}.phase-plan-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.phase-plan-grid label{display:grid;gap:5px}.phase-plan-grid select,.individual-order-row select,.opposition-order-row select{min-height:34px}.familiarity-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:10px}.familiarity-strip span{display:grid;padding:8px;background:var(--surface,#fff);border-radius:7px}.individual-order-row,.opposition-order-row{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:8px;align-items:center;padding:7px 0;border-top:1px solid var(--line,#d7dde6)}.individual-order-row>span,.opposition-order-row>span{display:grid}.opposition-layer p{color:var(--text-soft,#687386);font-size:11px}.opposition-order-row label{font-size:11px}.opposition-order-row{grid-template-columns:1.5fr .8fr .7fr .8fr}@media(max-width:1000px){.phase-plan-grid,.familiarity-strip{grid-template-columns:1fr 1fr}.individual-order-row,.opposition-order-row{grid-template-columns:1fr 1fr}}
</style>
