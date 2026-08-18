import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ENTITY_TYPES, buildNavigationHash, parseNavigationHash, safeEntityTab } from '../navigationRoute.js'

export const navigationGroups = [
  { label: 'HOY', items: [
    { id: 'home', label: 'Inicio' },
  ] },
  { label: 'EQUIPO', items: [
    { id: 'squad', label: 'Plantilla' },
    { id: 'tactics', label: 'Tácticas' },
    { id: 'training', label: 'Entrenamiento' },
  ] },
  { label: 'CLUB', items: [
    { id: 'market', label: 'Mercado' },
    { id: 'staff', label: 'Cuerpo técnico' },
    { id: 'economy', label: 'Economía' },
    { id: 'club', label: 'Club' },
  ] },
  { label: 'TEMPORADA', items: [
    { id: 'competitions', label: 'Competiciones' },
    { id: 'calendar', label: 'Calendario' },
    { id: 'news', label: 'Noticias' },
  ] },
  { label: 'CARRERA Y MUNDO', items: [
    { id: 'career', label: 'Carrera' },
    { id: 'national', label: 'Selecciones' },
    { id: 'history', label: 'Historia' },
    { id: 'champions', label: 'Campeones' },
  ] },
]

export function useNavigationContext({ liveMatch, lastMatchReport, matchActionBusy, flash, cancelPreviewAndNavigate }) {
  const view = ref('home')
  const routeEntity=ref(null)
  const routeEntityTab=ref('')
  const routeDepth=ref(Number(window.history.state?.m9394Depth||0))
  const sectionTitle = computed(() => view.value === 'match' ? 'Partido' : (navigationGroups.flatMap(group => group.items).find(item => item.id === view.value)?.label || 'Inicio'))
  const validViews = new Set(navigationGroups.flatMap(group => group.items.map(item => item.id)).concat(['match']))
  const canGoBack=computed(()=>routeDepth.value>0 || Boolean(routeEntity.value))
  let syncingHistory = false

  function replaceHistory(state,url){
    const depth=Number.isFinite(Number(window.history.state?.m9394Depth))?Number(window.history.state.m9394Depth):routeDepth.value
    routeDepth.value=Math.max(0,depth)
    window.history.replaceState({...state,m9394Depth:routeDepth.value},'',url)
  }
  function pushHistory(state,url){
    routeDepth.value=Math.max(0,routeDepth.value)+1
    window.history.pushState({...state,m9394Depth:routeDepth.value},'',url)
  }

  function replaceRoute(target) {
    syncingHistory = true
    view.value = target
    routeEntity.value=null
    routeEntityTab.value=''
    replaceHistory({ view: target },buildNavigationHash(target))
    queueMicrotask(() => { syncingHistory = false })
  }

  function openEntityRoute(type,id,{baseView=null,entityTab=''}={}){
    if(!ENTITY_TYPES.has(String(type))||id==null)return
    const target=baseView&&validViews.has(baseView)?baseView:view.value
    const entity={type:String(type),id:String(id)}
    const tab=safeEntityTab(entityTab)
    syncingHistory=true
    if(view.value!==target)view.value=target
    routeEntity.value=entity
    routeEntityTab.value=tab
    pushHistory({view:target,entity,entityTab:tab,entityEntry:true},buildNavigationHash(target,entity,{entityTab:tab}))
    queueMicrotask(()=>{syncingHistory=false})
  }

  function setEntityTab(tab){
    if(!routeEntity.value)return
    const next=safeEntityTab(tab)
    if(next===routeEntityTab.value)return
    syncingHistory=true
    routeEntityTab.value=next
    replaceHistory({view:view.value,entity:routeEntity.value,entityTab:next,entityEntry:true},buildNavigationHash(view.value,routeEntity.value,{entityTab:next}))
    queueMicrotask(()=>{syncingHistory=false})
  }

  function closeEntityRoute(){
    if(!routeEntity.value)return
    if(Number(window.history.state?.m9394Depth||0)>0){window.history.back();return}
    syncingHistory=true
    routeEntity.value=null
    routeEntityTab.value=''
    replaceHistory({view:view.value},buildNavigationHash(view.value))
    queueMicrotask(()=>{syncingHistory=false})
  }

  function navigateBack(){
    if(routeEntity.value){closeEntityRoute();return}
    if(routeDepth.value>0){window.history.back();return}
    if(view.value!=='home')replaceRoute('home')
  }

  function reconcileRouteAfterCareerLoad() {
    const {target:route,entity,entityTab}=parseNavigationHash()
    if (liveMatch.value && liveMatch.value.status !== 'finished') {
      const minute = Number(liveMatch.value.minute || 0)
      if (minute > 0 && !['match', 'tactics'].includes(route)) {
        replaceRoute('match'); flash('Partido recuperado tras recargar. Continúa desde el directo.'); return
      }
      if (minute === 0 && !['match', 'tactics'].includes(route)) {
        replaceRoute('match'); flash('Previa recuperada tras recargar. Puedes revisar XI o táctica antes de empezar.'); return
      }
    }
    if (route === 'match' && !liveMatch.value) {
      if (lastMatchReport.value?.committed) { liveMatch.value = lastMatchReport.value; replaceRoute('match'); return }
      replaceRoute('home'); return
    }
    if (route && validViews.has(route)){
      syncingHistory=true
      view.value=route;routeEntity.value=entity;routeEntityTab.value=entity?entityTab:''
      const depth=Number(window.history.state?.m9394Depth)
      routeDepth.value=Number.isFinite(depth)&&depth>=0?depth:0
      queueMicrotask(()=>{syncingHistory=false})
    }
  }

  async function applyRouteFromLocation() {
    const {target:route,entity,entityTab}=parseNavigationHash()
    if (!route || !validViews.has(route)) return
    const sameEntity=(routeEntity.value?.type||null)===(entity?.type||null) && String(routeEntity.value?.id||'')===String(entity?.id||'')
    const sameTab=routeEntityTab.value===(entity?entityTab:'')
    const depth=Number(window.history.state?.m9394Depth)
    routeDepth.value=Number.isFinite(depth)&&depth>=0?depth:Math.max(0,routeDepth.value-1)
    if (route === view.value && sameEntity && sameTab) return
    if (matchActionBusy.value && liveMatch.value) { replaceRoute('match'); flash('Hay una acción de partido en curso.'); return }
    if (liveMatch.value && liveMatch.value.status !== 'finished') {
      const minute = Number(liveMatch.value.minute || 0)
      if (minute > 0 && !['match', 'tactics'].includes(route)) {
        replaceRoute('match'); flash('El partido está en juego. Usa Directo, Táctica o Cambios hasta el final.'); return
      }
      if (minute === 0 && !['match', 'tactics'].includes(route)) {
        syncingHistory = true
        routeEntity.value=null;routeEntityTab.value=''
        await cancelPreviewAndNavigate(route)
        replaceHistory({ view: route },buildNavigationHash(route))
        queueMicrotask(() => { syncingHistory = false })
        return
      }
    }
    syncingHistory = true
    view.value = route
    routeEntity.value=entity
    routeEntityTab.value=entity?entityTab:''
    queueMicrotask(() => { syncingHistory = false })
  }

  watch(view, next => {
    if (syncingHistory || !validViews.has(next)) return
    routeEntity.value=null
    routeEntityTab.value=''
    const hash = buildNavigationHash(next)
    if (window.location.hash !== hash) pushHistory({ view: next },hash)
  })

  onMounted(() => {
    if(!Number.isFinite(Number(window.history.state?.m9394Depth))){replaceHistory({...(window.history.state||{}),view:parseNavigationHash().target},window.location.hash||'#home')}
    applyRouteFromLocation()
    window.addEventListener('popstate', applyRouteFromLocation)
    window.addEventListener('hashchange', applyRouteFromLocation)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('popstate', applyRouteFromLocation)
    window.removeEventListener('hashchange', applyRouteFromLocation)
  })

  return { view, routeEntity, routeEntityTab, routeDepth, canGoBack, sectionTitle, navigationGroups, replaceRoute, openEntityRoute, setEntityTab, closeEntityRoute, navigateBack, reconcileRouteAfterCareerLoad, applyRouteFromLocation }
}
