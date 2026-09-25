import { useState, useEffect } from 'react'
import AuthScreen from './components/AuthScreen'
import ChatScreen from './components/ChatScreen'

function App() {
  const [username, setUsername] = useState(null)
  const [ws, setWs] = useState(null)
  const [token, setToken] = useState(null)

  // Auto-login if token exists in localStorage
  useEffect(() => {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('username')
    if (savedToken && savedUser) {
      connectWebSocket(savedToken, savedUser)
    }
  }, [])

  const connectWebSocket = (jwt, name) => {
    const socket = new WebSocket(`ws://localhost:8000/ws?token=${jwt}`)

    socket.onopen = () => {
      setToken(jwt)
      setUsername(name)
      setWs(socket)
    }

    socket.onerror = () => {
      // Token might be expired — clear and show login
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      setToken(null)
      setUsername(null)
      setWs(null)
    }

    socket.onclose = (e) => {
      if (e.code === 4001) {
        // Server rejected token
        localStorage.removeItem('token')
        localStorage.removeItem('username')
        setToken(null)
        setUsername(null)
        setWs(null)
      }
    }
  }

  const handleAuth = (jwt, name) => {
    connectWebSocket(jwt, name)
  }

  const handleLogout = () => {
    if (ws) ws.close()
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    setToken(null)
    setUsername(null)
    setWs(null)
  }

  return username && ws ? (
    <ChatScreen username={username} ws={ws} onLogout={handleLogout} />
  ) : (
    <AuthScreen onAuth={handleAuth} />
  )
}

export default App
