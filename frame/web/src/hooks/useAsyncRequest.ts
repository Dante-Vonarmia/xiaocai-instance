import { useCallback, useEffect, useReducer, useRef } from 'react'

type AsyncRequestState<TData, TError> = {
  loading: boolean
  data: TData | undefined
  error: TError | undefined
}

type AsyncRequestAction<TData, TError> =
  | { type: 'start' }
  | { type: 'success'; payload: TData }
  | { type: 'failure'; payload: TError }
  | { type: 'set_data'; payload: TData | undefined }
  | { type: 'set_error'; payload: TError | undefined }
  | { type: 'set_loading'; payload: boolean }

type UseAsyncRequestOptions<TData, TError> = {
  canRequest?: () => boolean
  keepOneRequest?: boolean
  once?: boolean
  onThen?: (value: TData) => void
  onCatch?: (error: TError) => void
}

type PromiseWithAbort<TData> = Promise<TData> & { abort?: () => void }

const INITIAL_STATE: AsyncRequestState<unknown, unknown> = {
  loading: false,
  data: undefined,
  error: undefined,
}

function asyncRequestReducer<TData, TError>(
  state: AsyncRequestState<TData, TError>,
  action: AsyncRequestAction<TData, TError>,
): AsyncRequestState<TData, TError> {
  if (action.type === 'start') {
    return { ...state, loading: true, error: undefined }
  }
  if (action.type === 'success') {
    return { loading: false, data: action.payload, error: undefined }
  }
  if (action.type === 'failure') {
    return { ...state, loading: false, error: action.payload }
  }
  if (action.type === 'set_data') {
    return { ...state, data: action.payload }
  }
  if (action.type === 'set_error') {
    return { ...state, error: action.payload }
  }
  if (action.type === 'set_loading') {
    return { ...state, loading: action.payload }
  }
  return state
}

export function useAsyncRequest<TData, TParams extends unknown[] = unknown[], TError = unknown>(
  request: (...params: TParams) => PromiseWithAbort<TData> | Promise<TData>,
  options: UseAsyncRequestOptions<TData, TError> = {},
) {
  const { canRequest, keepOneRequest = false, once = false, onThen, onCatch } = options
  const [state, dispatch] = useReducer(
    asyncRequestReducer<TData, TError>,
    INITIAL_STATE as AsyncRequestState<TData, TError>,
  )
  const unmountedRef = useRef(false)
  const clientRef = useRef<PromiseWithAbort<TData> | null>(null)
  const onceExecutedRef = useRef(false)

  useEffect(() => () => {
    unmountedRef.current = true
    clientRef.current?.abort?.()
  }, [])

  const run = useCallback(async (...params: TParams) => {
    if (keepOneRequest) {
      clientRef.current?.abort?.()
    }

    if (canRequest && !canRequest()) {
      dispatch({ type: 'set_loading', payload: false })
      return undefined
    }

    dispatch({ type: 'start' })
    const current = request(...params) as PromiseWithAbort<TData>
    clientRef.current = current

    try {
      const result = await current
      if (unmountedRef.current) {
        return result
      }

      dispatch({ type: 'success', payload: result })
      if (onThen && (!once || !onceExecutedRef.current)) {
        onceExecutedRef.current = true
        onThen(result)
      }
      return result
    } catch (error) {
      if (unmountedRef.current) {
        return undefined
      }
      dispatch({ type: 'failure', payload: error as TError })
      if (onCatch && (!once || !onceExecutedRef.current)) {
        onceExecutedRef.current = true
        onCatch(error as TError)
      }
      throw error
    }
  }, [canRequest, keepOneRequest, onCatch, onThen, once, request])

  const abort = useCallback(() => {
    clientRef.current?.abort?.()
    clientRef.current = null
    dispatch({ type: 'set_loading', payload: false })
  }, [])

  const setData = useCallback((nextData: TData | undefined) => {
    dispatch({ type: 'set_data', payload: nextData })
  }, [])

  const setError = useCallback((nextError: TError | undefined) => {
    dispatch({ type: 'set_error', payload: nextError })
  }, [])

  const setLoading = useCallback((nextLoading: boolean) => {
    dispatch({ type: 'set_loading', payload: nextLoading })
  }, [])

  return {
    run,
    abort,
    loading: state.loading,
    data: state.data,
    error: state.error,
    setLoading,
    setData,
    setError,
  }
}
