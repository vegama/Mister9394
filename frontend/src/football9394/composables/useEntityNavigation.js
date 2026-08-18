import { ref, watch } from 'vue'
import { football9394Api } from '../api.js'

export function useEntityNavigation({
  careerId,
  routeEntity,
  routeEntityTab,
  selectedCompetition,
  careerCalendarRows,
  controlledTeam,
  calendarRowsForUi,
  profileFor,
  historicalPlayerPhoto,
  historicalClubCrest,
  formatSourceMoney,
  openEntityRoute,
  setEntityTab,
  replaceRoute,
  flash,
}) {
  const selectedPlayer = ref(null)
  const selectedTeamProfile = ref(null)
  const selectedMatchContext = ref(null)
  const entityLoadError = ref('')
  const entityLoading = ref(false)
  const playerTab = ref('profile')
  let requestSerial = 0

  function decoratePlayer(detail) {
    return {
      ...detail,
      photo_url: historicalPlayerPhoto(detail.id),
      team_crest_url: historicalClubCrest(detail.team_id),
      market_value_display: detail.transfer_value_is_exact === false
        ? `≈ ${formatSourceMoney(detail.estimated_transfer_value)}`
        : formatSourceMoney(detail.estimated_transfer_value),
    }
  }

  async function loadPlayerEntity(playerId, { fallback = null } = {}) {
    const request = ++requestSerial
    entityLoading.value = true
    if (fallback) selectedPlayer.value = profileFor(fallback)
    selectedTeamProfile.value = null
    selectedMatchContext.value = null
    playerTab.value = routeEntityTab.value || 'profile'
    entityLoadError.value = ''
    if (!careerId.value || !playerId) {
      if (request === requestSerial) entityLoading.value = false
      return
    }
    try {
      const detail = await football9394Api.careerPlayer(careerId.value, playerId)
      if (request === requestSerial && routeEntity.value?.type === 'player' && String(routeEntity.value.id) === String(playerId)) {
        selectedPlayer.value = decoratePlayer(detail)
      }
    } catch (error) {
      if (request === requestSerial) {
        entityLoadError.value = `No se pudo cargar la ficha del jugador: ${error.message}`
        flash(entityLoadError.value)
      }
    } finally {
      if (request === requestSerial) entityLoading.value = false
    }
  }

  async function loadTeamEntity(teamId) {
    const request = ++requestSerial
    entityLoading.value = true
    selectedPlayer.value = null
    selectedMatchContext.value = null
    selectedTeamProfile.value = null
    entityLoadError.value = ''
    if (!careerId.value || !teamId) {
      if (request === requestSerial) entityLoading.value = false
      return
    }
    try {
      const detail = await football9394Api.careerTeam(careerId.value, teamId)
      if (request === requestSerial && routeEntity.value?.type === 'team' && String(routeEntity.value.id) === String(teamId)) {
        selectedTeamProfile.value = detail
      }
    } catch (error) {
      if (request === requestSerial) {
        entityLoadError.value = `No se pudo cargar la ficha del club: ${error.message}`
        flash(entityLoadError.value)
      }
    } finally {
      if (request === requestSerial) entityLoading.value = false
    }
  }

  function openPlayer(row) {
    if (!row?.id) return
    selectedPlayer.value = profileFor(row)
    playerTab.value = 'profile'
    if (routeEntity.value?.type === 'player' && String(routeEntity.value.id) === String(row.id)) {
      loadPlayerEntity(row.id, { fallback: row })
      return
    }
    openEntityRoute('player', row.id, { entityTab: 'profile' })
  }

  function openTeam(teamId) {
    const id = Number(teamId || 0)
    if (!id) return
    if (routeEntity.value?.type === 'team' && String(routeEntity.value.id) === String(id)) {
      loadTeamEntity(id)
      return
    }
    openEntityRoute('team', id)
  }

  function openCompetitionEntity(payload) {
    const kind = String(payload?.kind || 'league')
    const sourceId = Number(payload?.sourceId || 0)
    if (!sourceId) return
    selectedCompetition.value = `${kind}:${sourceId}`
    openEntityRoute('competition', `${kind}:${sourceId}`, { baseView: 'competitions' })
  }

  function openMatchEntity(match) {
    if (!match?.id) return
    selectedMatchContext.value = match
    openEntityRoute('match', match.id, { baseView: 'calendar' })
  }

  function openNewsEntity(action) {
    if (action?.type === 'player') openEntityRoute('player', action.id, { baseView: 'news', entityTab: 'profile' })
    else if (action?.type === 'team') openEntityRoute('team', action.id, { baseView: 'news' })
    else if (action?.type === 'competition') openCompetitionEntity({ kind: action.kind || 'league', sourceId: action.id })
  }

  async function syncRouteEntity(entity) {
    entityLoadError.value = ''
    if (!entity) {
      requestSerial += 1
      entityLoading.value = false
      selectedPlayer.value = null
      selectedTeamProfile.value = null
      selectedMatchContext.value = null
      return
    }
    if (entity.type === 'player') {
      await loadPlayerEntity(entity.id)
      return
    }
    if (entity.type === 'team') {
      await loadTeamEntity(entity.id)
      return
    }
    if (entity.type === 'competition') {
      requestSerial += 1
      entityLoading.value = false
      selectedPlayer.value = null
      selectedTeamProfile.value = null
      selectedMatchContext.value = null
      const [kind, sourceId] = String(entity.id || '').split(':')
      if (kind && Number(sourceId)) {
        const key = `${kind}:${Number(sourceId)}`
        if (selectedCompetition.value !== key) selectedCompetition.value = key
      }
      return
    }
    if (entity.type === 'match') {
      const request = ++requestSerial
      entityLoading.value = true
      selectedPlayer.value = null
      selectedTeamProfile.value = null
      let raw = careerCalendarRows.value.find(row => String(row.id) === String(entity.id))
      if (!raw && careerId.value) {
        try {
          careerCalendarRows.value = await football9394Api.careerCalendar(careerId.value)
          raw = careerCalendarRows.value.find(row => String(row.id) === String(entity.id))
        } catch (error) {
          if (request === requestSerial) entityLoadError.value = `No se pudo recuperar el partido: ${error.message}`
        }
      }
      if (request === requestSerial) {
        selectedMatchContext.value = raw ? calendarRowsForUi([raw], { team: controlledTeam.value })[0] : null
        entityLoading.value = false
      }
      if (request === requestSerial && !selectedMatchContext.value) {
        entityLoadError.value = entityLoadError.value || 'Este partido ya no está disponible en el calendario actual.'
        flash(entityLoadError.value)
        replaceRoute('calendar')
      }
    }
  }

  async function retryRouteEntity() {
    if (!routeEntity.value) return
    await syncRouteEntity({ ...routeEntity.value })
  }

  watch(routeEntity, entity => syncRouteEntity(entity), { deep: true })
  watch(playerTab, tab => {
    if (routeEntity.value?.type === 'player') setEntityTab(tab)
  })

  return {
    selectedPlayer,
    selectedTeamProfile,
    selectedMatchContext,
    entityLoadError,
    entityLoading,
    playerTab,
    decoratePlayer,
    openPlayer,
    openTeam,
    openCompetitionEntity,
    openMatchEntity,
    openNewsEntity,
    retryRouteEntity,
  }
}
