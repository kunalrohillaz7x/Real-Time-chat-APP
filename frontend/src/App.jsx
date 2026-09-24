import { useState } from 'react'
import JoinScreen from './components/JoinScreen'
import ChatScreen from './components/ChatScreen'

function App() {
  const [username, setUsername] = useState(null)
  const [ws, setWs] = useState(null)

  const handleJoin = (name) => {
    // Connect to backend WebSocket
    const socket = new WebSocket(`ws://localhost:8000/ws/${name}`)

    socket.onopen = () => {
      setUsername(name)
      setWs(socket)
    }

    socket.onerror = () => {
      alert('Could not connect to the server. Is the backend running?')
    }
  }

  return username && ws ? (
    <ChatScreen username={username} ws={ws} />
  ) : (
    <JoinScreen onJoin={handleJoin} />
  )
}

export default App
