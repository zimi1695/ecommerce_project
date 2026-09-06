import { onScopeDispose, ref, shallowRef } from 'vue'
import { ApiError } from '../api/client'

export function useResource<T>() {
  const data = shallowRef<T | null>(null)
  const loading = ref(false)
  const error = shallowRef<ApiError | null>(null)
  let controller: AbortController | undefined
  let sequence = 0
  function clear() {
    sequence++
    controller?.abort()
    data.value = null
    error.value = null
    loading.value = false
  }
  async function load(fetcher: (signal: AbortSignal) => Promise<T>) {
    clear()
    const current = sequence
    controller = new AbortController()
    loading.value = true
    try {
      const result = await fetcher(controller.signal)
      if (current === sequence) data.value = result
    } catch (e) {
      if (current === sequence)
        error.value = e instanceof ApiError ? e : new ApiError(0, '数据加载失败，请重试。')
    } finally {
      if (current === sequence) loading.value = false
    }
  }
  onScopeDispose(clear)
  return { data, loading, error, load, clear }
}
