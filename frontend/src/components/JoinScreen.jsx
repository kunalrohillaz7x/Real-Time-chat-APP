import { useState, useRef } from 'react'

export default function JoinScreen({ onJoin }) {
  const [name, setName] = useState('')
  const inputRef = useRef(null)

  const handleJoin = () => {
    const trimmed = name.trim()
    if (trimmed) onJoin(trimmed)
  }

  return (
    <div className="join-screen">
      <h1>ChatWave</h1>
      <p>Enter your name to join the chat</p>
      <div className="join-form">
        <input
          ref={inputRef}
          type="text"
          placeholder="Your name..."
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleJoin()}
          autoFocus
        />
        <button onClick={handleJoin}>Join</button>
      </div>
    </div>
  )
}
