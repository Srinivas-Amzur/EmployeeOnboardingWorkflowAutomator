import { useEffect } from "react"
import { useCurrentUser } from "../../hooks"
import { useAuthStore } from "../../store"

export function AuthBootstrap() {
  const { data, error, isLoading } = useCurrentUser()
  const setUser = useAuthStore((state) => state.setUser)
  const setLoading = useAuthStore((state) => state.setLoading)
  const setInitialized = useAuthStore((state) => state.setInitialized)

  useEffect(() => {
    setLoading(isLoading)
    if (isLoading) {
      return
    }

    if (data) {
      setUser(data)
    }

    if (error) {
      setUser(null)
    }

    setInitialized(true)
  }, [data, error, isLoading, setInitialized, setLoading, setUser])

  return null
}