<script setup>
import { computed, ref } from 'vue'
import LineupPitch from './LineupPitch.vue'

const props = defineProps({
  squad: { type: Array, default: () => [] },
  lineupDraft: { type: Array, default: () => [] },
  lineupPlayers: { type: Array, default: () => [] },
  formation: { type: String, default: '4-4-2' },
  selection: { type: Object, default: () => ({}) },
  dressingRoom: { type: Object, default: () => ({captain_id:null,leaders:[],competitions:[],mentorships:[]}) },
})
const emit = defineEmits(['toggle-starter','open-player','renew','toggle-listing','auto-select','save-selection','open-tactics','set-captain'])

const query = ref('')
const position = ref('')
const availability = ref('all')
const sort = ref('overall')

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
const isStarter = id => props.lineupDraft.includes(Number(id))
const isCaptain = id => Number(props.dressingRoom?.captain_id||0)===Number(id)
const photo = id => id ? `/historical9394/players/${Number(id)}.jpg` : null
</script>

<template>
  <section class="screen-grid squad-screen redesigned-squad">
    <article class="football-panel roster modern-roster">
      <header class="panel-feature-head">
        <div><small>PRIMER EQUIPO</small><h2>Plantilla</h2><p>Selecciona el once, consulta el estado y entra en la ficha sin perder el contexto.</p></div>
        <div class="roster-kpis"><span><small>Plantilla</small><b>{{ squad.length }}</b></span><span><small>Media</small><b>{{ averageOverall }}</b></span><span><small>No disponibles</small><b>{{ unavailableCount }}</b></span><span><small>XI</small><b>{{ lineupDraft.length }}/11</b></span></div>
      </header>

      <div class="roster-toolbar">
        <label class="search-field"><span>Buscar</span><input v-model="query" type="search" placeholder="Nombre del jugador"></label>
        <label><span>Posición</span><select v-model="position"><option value="">Todas</option><option v-for="pos in positionOptions" :key="pos" :value="pos">{{pos}}</option></select></label>
        <label><span>Estado</span><select v-model="availability"><option value="all">Todos</option><option value="available">Disponibles</option><option value="unavailable">No disponibles</option></select></label>
        <label><span>Orden</span><select v-model="sort"><option value="overall">Media</option><option value="form">Forma</option><option value="position">Posición</option><option value="name">Nombre</option></select></label>
      </div>

      <div class="squad-rule-strip"><span>Puestos históricos especializados</span><span v-if="selection.foreign_rule">Extranjeros: máx. {{selection.foreign_rule.max_starting ?? '—'}} en XI · {{selection.foreign_rule.max_squad ?? 'sin tope'}} en convocatoria</span></div>
      <div class="roster-table-wrap">
        <table>
          <thead><tr><th>XI</th><th>Jugador</th><th>Pos.</th><th>Edad</th><th>Media</th><th>Forma</th><th>Moral</th><th>Contrato</th><th>Estado</th><th>Acciones</th></tr></thead>
          <tbody>
            <tr v-for="p in filteredSquad" :key="p.id" :class="{selectedStarter:isStarter(p.id)}" @dblclick="emit('open-player', p)">
              <td><button type="button" class="lineup-toggle" :class="{active:isStarter(p.id)}" :aria-label="isStarter(p.id) ? `Quitar a ${p.name} del once` : `Añadir a ${p.name} al once`" @click.stop="emit('toggle-starter', p)">{{isStarter(p.id)?'✓':'+'}}</button></td>
              <td><button type="button" class="player-cell" @click="emit('open-player', p)"><span class="roster-photo"><img :src="photo(p.id)" alt="" @error="$event.currentTarget.style.display='none'"></span><span><strong>{{p.name}} <em v-if="isCaptain(p.id)" class="captain-badge">C</em></strong><small>#{{p.n}} · {{p.nationality || '—'}} · {{p.profile?.squad_dynamics?.role || 'Plantilla'}}</small><small v-if="p.profile?.identity?.archetype" class="player-football-identity">{{p.profile.identity.archetype}} · encaje {{p.profile?.tactical_fit?.label || '—'}}</small></span></button></td>
              <td><span class="position-chip">{{p.pos}}</span></td><td>{{p.age}}</td><td class="rating-cell"><b>{{p.overall}}</b></td><td class="good-cell">{{p.form}}</td><td class="warn-cell">{{p.morale}}</td><td>{{p.contractEnd}}</td><td><span class="status-chip" :class="p.status==='DISP.'?'available':'unavailable'">{{p.status}}</span><small v-if="p.profile?.squad_dynamics?.satisfaction!=null" class="satisfaction-note">Ánimo rol {{p.profile.squad_dynamics.satisfaction}}/100</small></td>
              <td><div class="row-actions"><button v-if="!isCaptain(p.id)" type="button" class="icon-action" title="Nombrar capitán" @click.stop="emit('set-captain',p)">Capitán</button><button type="button" class="icon-action" title="Renovar" @click.stop="emit('renew',p)">Renovar</button><button type="button" class="icon-action" :class="{active:p.profile?.transfer_listed}" @click.stop="emit('toggle-listing',p)">{{p.profile?.transfer_listed?'Quitar mercado':'Transferible'}}</button></div></td>
            </tr>
            <tr v-if="!filteredSquad.length"><td colspan="10"><div class="table-empty">No hay jugadores que coincidan con estos filtros.</div></td></tr>
          </tbody>
        </table>
      </div>
    </article>

    <aside class="football-panel lineup modern-lineup-card">
      <div class="squad-decision-pulse d6-squad-pulse">
        <span><small>ENCAJE DEL XI</small><b>{{lineupFit ?? '—'}}<em v-if="lineupFit!=null">/100</em></b></span>
        <span><small>TENSIONES</small><b>{{tensions.length}}</b><em>{{tensions.length?tensions.map(p=>p.name).join(' · '):'vestuario estable'}}</em></span>
        <span><small>RIESGO XI</small><b>{{fragileStarters.length}}</b><em>{{fragileStarters.length?'revisa disponibilidad':'sin alertas'}}</em></span>
      </div>
      <div class="lineup-card-head"><span><small>ONCE ACTUAL</small><strong>{{formation}}</strong></span><b :class="lineupDraft.length===11?'ready':'pending'">{{lineupDraft.length===11?'LISTO':'INCOMPLETO'}}</b></div>
      <LineupPitch :formation="formation" :players="lineupPlayers" compact />
      <div v-if="selection.issues?.length" class="selection-message error">{{selection.issues.join(' ')}}</div>
      <div v-if="selection.warnings?.length" class="selection-message warning">{{selection.warnings.join(' ')}}</div>
      <section class="dressing-room-card">
        <header><span><small>VESTUARIO</small><strong>Jerarquía y competencia</strong></span><b>{{dressingRoom.leaders?.length || 0}} líderes</b></header>
        <div class="leadership-strip"><span v-for="leader in dressingRoom.leaders?.slice(0,4)" :key="leader.player_id"><b>{{leader.captain?'C · ':''}}{{leader.name}}</b><small>{{leader.relationship}} · liderazgo {{Math.round(leader.score)}}</small></span></div>
        <div v-if="dressingRoom.competitions?.length" class="competition-list"><small>BATALLAS POR EL PUESTO</small><span v-for="battle in dressingRoom.competitions.slice(0,3)" :key="battle.slot"><b>{{battle.slot}}</b><em>tensión {{battle.heat}}/100</em></span></div>
        <div v-if="dressingRoom.mentorships?.length" class="mentorship-list"><small>TUTELAS</small><span v-for="pair in dressingRoom.mentorships.slice(0,2)" :key="pair.protege_id">{{pair.mentor_name}} → {{pair.protege_name}}</span></div>
      </section>
      <div class="lineup-actions"><button type="button" class="football-button" @click="emit('auto-select')">Mejor once disponible</button><button type="button" class="football-button primary" @click="emit('save-selection')">Guardar once</button><button type="button" class="football-button" @click="emit('open-tactics')">Abrir táctica</button></div>
    </aside>
  </section>
</template>
