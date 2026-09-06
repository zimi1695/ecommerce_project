import JSONbig from 'json-bigint'

const parser = JSONbig({ storeAsString: true, protoAction: 'error', constructorAction: 'error' })
export const isMock = import.meta.env.VITE_USE_MOCK === 'true'
export const apiBase = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

function normalize(value: unknown, key = ''): unknown {
  if (value === null) return null
  if (key.endsWith('_id')) return String(value)
  if (Array.isArray(value)) return value.map((item) => normalize(item))
  if (typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([k, v]) => [k, normalize(v, k)]),
    )
  }
  return value
}

export function parseResponse<T>(raw: string): T {
  return normalize(parser.parse(raw)) as T
}

export async function request<T>(
  path: string,
  params: Record<string, string | number | undefined> = {},
  signal?: AbortSignal,
): Promise<T> {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value))
  })
  const controller = new AbortController()
  const abort = () => controller.abort()
  if (signal?.aborted) controller.abort()
  signal?.addEventListener('abort', abort, { once: true })
  let timedOut = false
  const timer = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, 30_000)
  try {
    const response = await fetch(`${apiBase}${path}${query.size ? `?${query}` : ''}`, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
    })
    const raw = await response.text()
    let data: unknown
    try {
      data = parseResponse(raw)
    } catch {
      throw new ApiError(
        response.ok ? 502 : response.status,
        '接口返回了无法解析的数据，请联系负责人检查服务。',
      )
    }
    if (!response.ok) {
      const message =
        typeof data === 'object' && data && 'message' in data ? String(data.message) : '请求失败'
      throw new ApiError(response.status, message)
    }
    return data as T
  } catch (error) {
    if (timedOut) throw new ApiError(408, '请求超时，请稍后重试。')
    if (error instanceof ApiError || controller.signal.aborted) throw error
    throw new ApiError(0, '无法连接数据服务，请检查网络或联系负责人。')
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', abort)
  }
}
