<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import LineupPitch from './LineupPitch.vue'
import UiPageHeader from '../../components/ui/UiPageHeader.vue'
import UiActionDock from '../../components/ui/UiActionDock.vue'
import UiEmptyState from '../../components/ui/UiEmptyState.vue'
import UiDataTable from '../../components/ui/UiDataTable.vue'

const props = defineProps({
  squad: { type: Array, default: () => [] },
  lineupDraft: { type: Array, default: () => [] },
  lineupPlayers: { type: Array, default: () => [] },
  benchDraft: { type: Array, default: () => [] },
  benchPlayers: { type: Array, default: () => [] },
  formation: { type: String, default: '4-4-2' },
  selection: { type: Object, default: () => ({}) },
  dressingRoom: { type: Object, default: () => ({captain_id:null,leaders:[],competitions:[],mentorships:[]}) },
})
const emit = defineEmits(['toggle-starter','toggle-bench','replace-starter','replace-bench','open-player','renew','toggle-listing','auto-select','save-selection','open-tactics','set-captain','respond-concern','discipline'])

const query = ref('')
const position = ref('')
const availability = ref('all')
const sort = ref('overall')
const replaceTarget = ref(null)
const squadViewStorageKey = 'mister9394:squad-view:v1'

onMounted(() => {
  try {
    const stored = JSON.parse(sessionStorage.getItem(squadViewStorageKey) || '{}')
    if (typeof stored.query === 'string') query.value = stored.query
    if (typeof stored.position === 'string') position.value = stored.position
    if (['all','available','unavailable'].includes(stored.availability)) availability.value = stored.availability
    if (['overall','form','position','name'].includes(stored.sort)) sort.value = stored.sort
  } catch (_) {}
})
watch([query, position, availability, sort], () => {
  try {
    sessionStorage.setItem(squadViewStorageKey, JSON.stringify({
      query: query.value,
      position: position.value,
      availability: availability.value,
      sort: sort.value,
    }))
  } catch (_) {}
})

const positionOptions = computed(() => [...new Set(props.squad.map(p => p.pos).filter(Boolean))].sort())
const unavailableCount = computed(() => props.squad.filter(p => p.status !== 'DISP.').length)
const averageOverall = computed(() => {
  const values = props.squad.map(p => Number(p.overall)).filter(Number.isFinite)
  return values.length ? Math.round(values.reduce((a,b)=>a+b,0) / values.length) : '—'
})
const filteredSquad = computed(() => {
  const needle = query.value.trim().toLocaleLowerCase('es')
  const rows = props.squad.filter(p => {
    if (needle && !String(p.name || '').toLocaleLowerCase('es').includes(needle)) return false
    if (position.value && p.pos !== position.value) return false
    if (availability.value === 'available' && p.status !== 'DISP.') return false
    if (availability.value === 'unavailable' && p.status === 'DISP.') return false
    return true
  })
  const key = sort.value
  return [...rows].sort((a,b) => {
    if (key === 'name') return String(a.name).localeCompare(String(b.name), 'es')
    if (key === 'position') return String(a.pos).localeCompare(String(b.pos), 'es') || Number(b.overall||0)-Number(a.overall||0)
    if (key === 'form') return Number(b.form||0)-Number(a.form||0)
    return Number(b.overall||0)-Number(a.overall||0)
  })
})

const lineupFit = computed(() => {
  const values=props.lineupPlayers.map(p=>Number(p.profile?.tactical_fit?.score ?? 0)).filter(v=>v>0)
  return values.length?Math.round(values.reduce((a,b)=>a+b,0)/values.length):null
})
const tensions = computed(() => props.squad.filter(p=>p.profile?.squad_dynamics?.wants_move || Number(p.profile?.squad_dynamics?.satisfaction||100)<45).slice(0,4))
const fragileStarters = computed(() => props.lineupPlayers.filter(p=>p.status!=='DISP.' || Number(p.profile?.condition ?? p.profile?.match_condition ?? 100)<70).slice(0,3))
const savedStarterIds = computed(() => [...(props.selection?.starter_ids || [])].map(Number).sort((a,b)=>a-b))
const draftStarterIds = computed(() => [...props.lineupDraft].map(Number).sort((a,b)=>a-b))
const savedBenchIds = computed(() => [...(props.selection?.bench_ids || [])].map(Number).sort((a,b)=>a-b))
const draftBenchIds = computed(() => [...props.benchDraft].map(Number).sort((a,b)=>a-b))
const hasLineupChanges = computed(() => JSON.stringify(savedStarterIds.value)!==JSON.stringify(draftStarterIds.value) || JSON.stringify(savedBenchIds.value)!==JSON.stringify(draftBenchIds.value))
const draftComplete = computed(() => props.lineupDraft.length===11 && props.benchDraft.length===5)
const lineupStateLabel = computed(() => hasLineupChanges.value ? (draftComplete.value?'SIN GUARDAR':'INCOMPLETA') : (props.selection?.valid && draftComplete.value?'LISTA':'REVISAR'))
const isStarter = id => props.lineupDraft.includes(Number(id))
const isBench = id => props.benchDraft.includes(Number(id))
const isCaptain = id => Number(props.dressingRoom?.captain_id||0)===Number(id)
const photo = id => id ? `/historical9394/players/${Number(id)}.jpg` : null
const restCandidates = computed(() => [...props.squad]
  .filter(p => !isStarter(p.id) && !isBench(p.id))
  .sort((a,b) => (a.status==='DISP.'?0:1)-(b.status==='DISP.'?0:1) || Number(b.overall||0)-Number(a.overall||0)))

const choosePitchPlayer = player => { replaceTarget.value = player || null }
const cancelReplace = () => { replaceTarget.value = null }
const removeReplaceTarget = () => { if (!replaceTarget.value) return; emit('toggle-starter', replaceTarget.value); replaceTarget.value = null }
function lineupAction(player) {
  if (replaceTarget.value && Number(replaceTarget.value.id)!==Number(player.id)) {
    emit('replace-starter',{sourceId:Number(player.id),targetId:Number(replaceTarget.value.id)})
    replaceTarget.value=null
    return
  }
  emit('toggle-starter', player)
}
function dragPlayer(event, player) {
  if (!player || player.status!=='DISP.') return
  event.dataTransfer.effectAllowed='move'
  event.dataTransfer.setData('application/x-mister-player', String(player.id))
  event.dataTransfer.setData('text/plain', String(player.id))
}
function dropOnBench(event, target=null) {
  event.preventDefault()
  const sourceId=Number(event.dataTransfer.getData('application/x-mister-player') || event.dataTransfer.getData('text/plain'))
  if (sourceId) emit('replace-bench',{sourceId,targetId:Number(target?.id||0)})
}
</script>

<template>
  <section class="screen-grid squad-screen redesigned-squad">
    <article class="football-panel roster modern-roster">
      <UiPageHeader eyebrow="PRIMER EQUIPO" title="Plantilla" description="Construye la convocatoria completa, compara disponibilidad y entra en cada ficha sin perder el contexto." :status="`${filteredSquad.length} visibles`">
        <template #actions><div class="roster-kpis">
          <span><small>Plantilla</small><b>{{ squad.length }}</b></span>
          <span><small>Media</small><b>{{ averageOverall }}</b></span>
          <span><small>No disponibles</small><b>{{ unavailableCount }}</b></span>
          <span class="selection-kpi"><small>Convocatoria</small><b>{{ lineupDraft.length + benchDraft.length }}/16</b><em>{{lineupDraft.length}} XI · {{benchDraft.length}} banquillo</em></span>
        </div></template>
      </UiPageHeader>

      <div class="roster-toolbar">
        <label class="search-field"><span>Buscar</span><input v-model="query" type="search" placeholder="Nombre del jugador"></label>
        <label><span>Posición</span><select v-model="position"><option value="">Todas</option><option v-for="pos in positionOptions" :key="pos" :value="pos">{{pos}}</option></select></label>
        <label><span>Estado</span><select v-model="availability"><option value="all">Todos</option><option value="available">Disponibles</option><option value="unavailable">No disponibles</option></select></label>
        <label><span>Orden</span><select v-model="sort"><option value="overall">Media</option><option value="form">Forma</option><option value="position">Posición</option><option value="name">Nombre</option></select></label>
      </div>

      <div class="squad-rule-strip"><span>Puestos históricos especializados</span><span>Convocatoria: 11 titulares + 5 suplentes</span><span v-if="selection.foreign_rule">Extranjeros: máx. {{selection.foreign_rule.max_starting ?? '—'}} en XI · {{selection.foreign_rule.max_squad ?? 'sin tope'}} en convocatoria</span></div>
      <UiDataTable class="roster-table-wrap" aria-label="Plantilla del primer equipo" sticky>
          <thead><tr><th>Conv.</th><th>Jugador</th><th>Pos.</th><th>Edad</th><th>Media</th><th>Forma</th><th>Moral</th><th>Contrato</th><th>Estado</th><th>Acciones</th></tr></thead>
          <tbody>
            <tr v-for="p in filteredSquad" :key="p.id" :class="{selectedStarter:isStarter(p.id),selectedBench:isBench(p.id)}" @dblclick="emit('open-player', p)">
              <td><div class="selection-cell"><button type="button" class="lineup-toggle" :class="{active:isStarter(p.id)}" :disabled="p.status!=='DISP.'&&!isStarter(p.id)" @click.stop="lineupAction(p)">{{isStarter(p.id)?'XI ✓':'XI'}}</button><button type="button" class="bench-toggle" :class="{active:isBench(p.id)}" :disabled="isStarter(p.id) || (p.status!=='DISP.'&&!isBench(p.id))" @click.stop="emit('toggle-bench',p)">{{isBench(p.id)?'B ✓':'B'}}</button></div></td>
              <td><button type="button" class="player-cell" @click="emit('open-player', p)"><span class="roster-photo"><img :src="photo(p.id)" alt="" @error="$event.currentTarget.style.display='none'"></span><span><strong>{{p.name}} <em v-if="isCaptain(p.id)" class="captain-badge">C</em></strong><small>#{{p.n}} · {{p.nationality || '—'}} · {{p.profile?.squad_dynamics?.role || 'Plantilla'}}</small><small v-if="p.profile?.identity?.archetype" class="player-football-identity">{{p.profile.identity.archetype}} · encaje {{p.profile?.tactical_fit?.label || '—'}}</small></span></button></td>
              <td><span class="position-chip">{{p.pos}}</span></td><td>{{p.age}}</td><td class="rating-cell"><b>{{p.overall}}</b></td><td class="good-cell">{{p.form}}</td><td class="warn-cell">{{p.morale}}</td><td>{{p.contractEnd}}</td><td><span class="status-chip" :class="p.status==='DISP.'?'available':'unavailable'">{{p.status}}</span><small v-if="p.profile?.squad_dynamics?.satisfaction!=null" class="satisfaction-note">Ánimo rol {{p.profile.squad_dynamics.satisfaction}}/100</small></td>
              <td><div class="row-actions"><button v-if="!isCaptain(p.id)" type="button" class="icon-action" title="Nombrar capitán" @click.stop="emit('set-captain',p)">Capitán</button><button type="button" class="icon-action" title="Renovar" @click.stop="emit('renew',p)">Renovar</button><button type="button" class="icon-action" :class="{active:p.profile?.transfer_listed}" @click.stop="emit('toggle-listing',p)">{{p.profile?.transfer_listed?'Quitar mercado':'Transferible'}}</button></div></td>
            </tr>
            <tr v-if="!filteredSquad.length"><td colspan="10"><UiEmptyState compact icon="⌕" title="No hay jugadores con estos filtros" description="La plantilla sigue intacta: cambia búsqueda, posición o disponibilidad para volver a ver jugadores." /></td></tr>
          </tbody>
      </UiDataTable>
    </article>

    <aside class="football-panel lineup modern-lineup-card">
      <div class="squad-decision-pulse d6-squad-pulse">
        <span><small>ENCAJE DEL XI</small><b>{{lineupFit ?? '—'}}<em v-if="lineupFit!=null">/100</em></b></span>
        <span><small>TENSIONES</small><b>{{tensions.length}}</b><em>{{tensions.length?tensions.map(p=>p.name).join(' · '):'vestuario estable'}}</em></span>
        <span><small>RIESGO XI</small><b>{{fragileStarters.length}}</b><em>{{fragileStarters.length?'revisa disponibilidad':'sin alertas'}}</em></span>
      </div>
      <div class="lineup-card-head"><span><small>CONVOCATORIA ACTUAL</small><strong>{{formation}}</strong><em>{{lineupDraft.length}}/11 titulares · {{benchDraft.length}}/5 suplentes</em></span><b :class="!hasLineupChanges && selection.valid && draftComplete?'ready':'pending'">{{lineupStateLabel}}</b></div>
      <LineupPitch :formation="formation" :players="lineupPlayers" compact interactive draggable :selected-player-id="Number(replaceTarget?.id||0)" @select-player="choosePitchPlayer" @drop-player="emit('replace-starter',$event)" />
      <div class="lineup-builder-help" :class="{active:replaceTarget}">
        <template v-if="replaceTarget"><span><small>CAMBIO EN EL XI</small><strong>{{replaceTarget.name}}</strong><em>Arrastra un suplente sobre su foto o pulsa un candidato para sustituirlo.</em></span><div><button type="button" @click="removeReplaceTarget">Quitar del XI</button><button type="button" @click="cancelReplace">Cancelar</button></div></template>
        <template v-else><span><small>SELECCIÓN DIRECTA</small><strong>Arrastra para cambiar titulares</strong><em>Los dorsales van separados de la foto. Arrastra un jugador del banquillo o del resto de plantilla sobre el titular que quieras cambiar.</em></span></template>
      </div>

      <section class="matchday-bench-card">
        <header><span><small>BANQUILLO</small><strong>5 suplentes</strong></span><b :class="{complete:benchDraft.length===5}">{{benchDraft.length}}/5</b></header>
        <div class="matchday-bench-grid">
          <article v-for="p in benchPlayers" :key="p.id" class="matchday-bench-player" draggable="true" @dragstart="dragPlayer($event,p)" @dragover.prevent @drop="dropOnBench($event,p)">
            <span class="lineup-bench-photo"><img :src="photo(p.id)" alt="" @error="$event.currentTarget.style.display='none'"></span>
            <span><strong>{{p.name}}</strong><small>#{{p.n}} · {{p.pos}} · {{p.overall}}</small></span>
            <button type="button" title="Quitar del banquillo" @click="emit('toggle-bench',p)">×</button>
          </article>
          <article v-for="n in Math.max(0,5-benchPlayers.length)" :key="`empty-${n}`" class="matchday-bench-player empty" @dragover.prevent @drop="dropOnBench($event)"><span>{{n}}</span><strong>Plaza libre</strong><small>Arrastra aquí o usa “B”</small></article>
        </div>
      </section>

      <section class="lineup-bench-picker" :class="{choosing:replaceTarget}">
        <header><span><small>{{replaceTarget ? 'ELIGE SUSTITUTO' : 'RESTO DE PLANTILLA'}}</small><strong>{{replaceTarget ? `Por ${replaceTarget.name}` : 'Disponibles fuera de convocatoria'}}</strong></span><b>{{restCandidates.filter(p=>p.status==='DISP.').length}} aptos</b></header>
        <div class="lineup-bench-list">
          <div v-for="p in restCandidates" :key="p.id" class="lineup-bench-player rest-player" :class="{disabled:p.status!=='DISP.'}" :draggable="p.status==='DISP.'" @dragstart="dragPlayer($event,p)">
            <span class="lineup-bench-photo"><img :src="photo(p.id)" alt="" @error="$event.currentTarget.style.display='none'"></span>
            <span class="lineup-bench-copy"><strong>{{p.name}}</strong><small>{{p.pos}} · {{p.overall}} · {{p.status}}</small></span>
            <div><button type="button" :disabled="p.status!=='DISP.'" @click="lineupAction(p)">{{replaceTarget ? 'Al XI' : 'XI'}}</button><button type="button" :disabled="p.status!=='DISP.' || benchDraft.length>=5" @click="emit('toggle-bench',p)">Banquillo</button></div>
          </div>
        </div>
      </section>
      <div v-if="hasLineupChanges && !draftComplete" class="selection-message warning">Convocatoria incompleta: {{lineupDraft.length}}/11 titulares y {{benchDraft.length}}/5 suplentes.</div>
      <div v-if="!hasLineupChanges && selection.issues?.length" class="selection-message error">{{selection.issues.join(' ')}}</div>
      <div v-if="!hasLineupChanges && selection.warnings?.length" class="selection-message warning">{{selection.warnings.join(' ')}}</div>
      <section class="dressing-room-card">
        <header><span><small>VESTUARIO</small><strong>Jerarquía y competencia</strong></span><b>{{dressingRoom.leaders?.length || 0}} líderes</b></header>
        <div class="leadership-strip"><span v-for="leader in dressingRoom.leaders?.slice(0,4)" :key="leader.player_id"><b>{{leader.captain?'C · ':''}}{{leader.name}}</b><small>{{leader.relationship}} · liderazgo {{Math.round(leader.score)}}</small></span></div>
        <div v-if="dressingRoom.competitions?.length" class="competition-list"><small>BATALLAS POR EL PUESTO</small><span v-for="battle in dressingRoom.competitions.slice(0,3)" :key="battle.slot"><b>{{battle.slot}}</b><em>tensión {{battle.heat}}/100</em></span></div>
        <div class="dressing-cohesion"><small>COHESIÓN</small><b>{{dressingRoom.squad_cohesion ?? '—'}}<em v-if="dressingRoom.squad_cohesion!=null">/100</em></b><span>{{(dressingRoom.social_groups||[]).length}} grupos sociales detectados</span></div>
        <div v-if="dressingRoom.mentorships?.length" class="mentorship-list"><small>TUTELAS</small><span v-for="pair in dressingRoom.mentorships.slice(0,2)" :key="pair.protege_id">{{pair.mentor_name}} → {{pair.protege_name}}</span></div>
      </section>
      <UiActionDock class="lineup-flow-actions" eyebrow="SIGUIENTE PASO" :title="hasLineupChanges?'Guarda la convocatoria completa':'Convocatoria sincronizada con la carrera'" :detail="draftComplete?'El once y los cinco suplentes están completos.':'Necesitas 11 titulares y 5 suplentes para llegar al partido.'" :tone="!draftComplete?'warning':'accent'" sticky><button type="button" class="football-button" @click="emit('auto-select')">Mejor 11 + 5</button><button type="button" class="football-button" :disabled="!hasLineupChanges || !draftComplete" @click="emit('save-selection')">Guardar convocatoria</button><button type="button" class="football-button primary" :disabled="!draftComplete" @click="emit('open-tactics')">{{hasLineupChanges?'Guardar y abrir táctica':'Abrir táctica'}} →</button></UiActionDock>
    </aside>
  </section>
</template>

<style scoped>
.selection-cell{display:flex;gap:5px}.bench-toggle{min-width:34px;min-height:28px;border:1px solid var(--f-line);border-radius:7px;background:var(--f-panel2);color:var(--f-muted);font-size:11px;font-weight:850}.bench-toggle.active{border-color:#2a9465;background:#143c2d;color:#74e1a2}.selection-kpi em{font-size:11px;font-style:normal;color:var(--f-muted)}
.matchday-bench-card{margin:0 12px 10px;border:1px solid var(--f-line);border-radius:11px;background:var(--f-panel);overflow:hidden}.matchday-bench-card>header{display:flex;justify-content:space-between;align-items:end;padding:9px 10px;border-bottom:1px solid var(--f-line);background:var(--f-panel2)}.matchday-bench-card>header span{display:grid}.matchday-bench-card>header small{font-size:11px;font-weight:900;letter-spacing:.08em;color:var(--f-muted)}.matchday-bench-card>header b{padding:4px 7px;border-radius:999px;background:#3b2e13;color:#e2bd61;font-size:11px}.matchday-bench-card>header b.complete{background:#163a2c;color:#6ad698}.matchday-bench-grid{display:grid;grid-template-columns:1fr;max-height:232px;overflow:auto}.matchday-bench-player{display:grid;grid-template-columns:34px minmax(0,1fr) auto;gap:8px;align-items:center;min-height:50px;padding:5px 8px;border-bottom:1px solid var(--f-line);cursor:grab}.matchday-bench-player:last-child{border-bottom:0}.matchday-bench-player>span:nth-child(2){display:grid;gap:1px;min-width:0}.matchday-bench-player strong{font-size:11px}.matchday-bench-player small{font-size:11px;color:var(--f-muted)}.matchday-bench-player>button{width:26px;height:26px;border:1px solid var(--f-line);border-radius:7px;background:transparent;color:var(--f-muted)}.matchday-bench-player.empty{grid-template-columns:28px 1fr;color:var(--f-muted);cursor:default}.matchday-bench-player.empty>span{display:grid;place-items:center;width:24px;height:24px;border:1px dashed var(--f-line-strong);border-radius:50%;font-size:11px}
.rest-player{cursor:grab}.rest-player.disabled{opacity:.45;cursor:not-allowed}.rest-player>div{display:flex;gap:4px}.rest-player>div button{min-height:28px;border:1px solid var(--f-line);border-radius:7px;background:var(--f-panel2);color:var(--f-text);padding:0 7px;font-size:11px;font-weight:800}.rest-player>div button:disabled{opacity:.4}.dressing-cohesion{display:grid;grid-template-columns:1fr auto;gap:2px 10px;padding:9px 0;border-top:1px solid var(--f-line)}.dressing-cohesion small{grid-column:1/-1;font-size:11px;font-weight:800;letter-spacing:.07em;color:var(--f-muted)}.dressing-cohesion b em{font-size:11px;font-style:normal}.dressing-cohesion span{font-size:11px;color:var(--f-muted)}
.lineup-card-head span{display:grid}.lineup-card-head span em{font-size:11px;font-style:normal;color:var(--f-muted)}.lineup-flow-actions{position:sticky;bottom:0;z-index:4;display:flex;align-items:center;gap:7px;padding:10px 0 2px;background:linear-gradient(to top,var(--f-panel) 82%,transparent)}.lineup-flow-copy{display:grid;margin-right:auto;min-width:190px}.lineup-flow-copy small{font-size:11px;font-weight:900;letter-spacing:.08em;color:var(--f-muted)}.lineup-flow-copy strong{font-size:11px}@media(max-width:1000px){.lineup-flow-actions{position:static;flex-wrap:wrap}.lineup-flow-copy{width:100%}}
</style>
