import { ref } from 'vue'

export function useCareerState({
  marketQuery, marketPosition, marketFreeAgents, marketWatchedOnly, selectedTarget, restoredMarketTargetId,
  selectedCompetition, competitionViewMode, newsCategory,
}) {
  const careerId = ref('')

  function setCareerId(id) {
    careerId.value = String(id || '')
    if (careerId.value) window.localStorage?.setItem('mister9394-career-id', careerId.value)
  }

  function marketWorkspaceStorageKey(id = careerId.value) {
    return id ? `mister9394-market-workspace:${id}` : ''
  }
  function persistMarketWorkspace() {
    const key = marketWorkspaceStorageKey(); if (!key) return
    try {
      window.sessionStorage?.setItem(key, JSON.stringify({
        query: marketQuery.value, position: marketPosition.value, freeAgents: marketFreeAgents.value,
        watchedOnly: marketWatchedOnly.value, selectedTargetId: selectedTarget.value?.[5] ?? null,
      }))
    } catch {}
  }
  function restoreMarketWorkspace(id) {
    const key = marketWorkspaceStorageKey(id); if (!key) return
    try {
      const raw = JSON.parse(window.sessionStorage?.getItem(key) || 'null'); if (!raw) return
      marketQuery.value = String(raw.query || '')
      marketPosition.value = String(raw.position || '')
      marketFreeAgents.value = Boolean(raw.freeAgents)
      marketWatchedOnly.value = Boolean(raw.watchedOnly)
      restoredMarketTargetId.value = raw.selectedTargetId ? Number(raw.selectedTargetId) : null
    } catch {}
  }

  function dailyWorkspaceStorageKey(id = careerId.value) {
    return id ? `mister9394-daily-workspace:${id}` : ''
  }
  function persistDailyWorkspace() {
    const key = dailyWorkspaceStorageKey(); if (!key) return
    try {
      window.sessionStorage?.setItem(key, JSON.stringify({
        competition: selectedCompetition.value,
        competitionViewMode: competitionViewMode.value,
        newsCategory: newsCategory.value,
      }))
    } catch {}
  }
  function restoreDailyWorkspace(id) {
    const key = dailyWorkspaceStorageKey(id); if (!key) return
    try {
      const raw = JSON.parse(window.sessionStorage?.getItem(key) || 'null'); if (!raw) return
      if (raw.competition) selectedCompetition.value = String(raw.competition)
      if (['table', 'results', 'calendar', 'honours'].includes(String(raw.competitionViewMode || ''))) {
        competitionViewMode.value = String(raw.competitionViewMode)
      }
      if (raw.newsCategory) newsCategory.value = String(raw.newsCategory)
    } catch {}
  }

  return {
    careerId, setCareerId,
    persistMarketWorkspace, restoreMarketWorkspace,
    persistDailyWorkspace, restoreDailyWorkspace,
  }
}
