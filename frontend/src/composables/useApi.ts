import { ref } from 'vue'
import type { AxiosResponse } from 'axios'

interface UseApiOptions<T> {
  immediate?: boolean
  defaultValue?: T
  onSuccess?: (data: T) => void
  onError?: (err: Error) => void
}

export function useApi<T>(
  fetcher: () => Promise<AxiosResponse<T>>,
  options: UseApiOptions<T> = {}
) {
  const { immediate = false, defaultValue, onSuccess, onError } = options

  const data = ref<T | undefined>(defaultValue)
  const loading = ref(false)
  const error = ref<Error | null>(null)

  async function execute() {
    loading.value = true
    error.value = null
    try {
      const res = await fetcher()
      data.value = res.data
      onSuccess?.(res.data)
      return res.data
    } catch (err) {
      const e = err instanceof Error ? err : new Error(String(err))
      error.value = e
      onError?.(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  if (immediate) {
    execute()
  }

  return {
    data,
    loading,
    error,
    execute,
    refresh: execute,
  }
}
