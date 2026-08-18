import { ref, watch } from 'vue'

export function useFirstRunGuide({ careerId, careerRecords }) {
  const firstRunGuideVisible = ref(false)
  const storageKey = (id = careerId.value) => id ? `mister9394:first-run-guide:v1:${id}` : ''

  function refreshFirstRunGuide() {
    const key = storageKey()
    firstRunGuideVisible.value = Boolean(key && !window.localStorage?.getItem(key) && Number(careerRecords.value?.matches_managed || 0) === 0)
  }

  function dismissFirstRunGuide() {
    const key = storageKey()
    if (key) window.localStorage?.setItem(key, 'dismissed')
    firstRunGuideVisible.value = false
  }

  watch(() => careerRecords.value?.matches_managed, refreshFirstRunGuide)
  return { firstRunGuideVisible, refreshFirstRunGuide, dismissFirstRunGuide }
}
