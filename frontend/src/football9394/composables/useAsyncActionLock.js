import { ref } from 'vue'

export function useAsyncActionLock() {
  const busy = ref(false)

  async function run(task) {
    if (busy.value) return null
    busy.value = true
    try {
      return await task()
    } finally {
      busy.value = false
    }
  }

  return { busy, run }
}
