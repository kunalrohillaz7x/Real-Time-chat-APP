import { useState, useRef, useEffect } from 'react'

export default function ChatScreen({ username, ws, onLogout }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [connected, setConnected] = useState(true)
  const messagesEndRef = useRef(null)

  // Listen for WebSocket messages
  useEffect(() => {
    if (!ws) return

    ws.onmessage = (event) => {
      const data = event.data

      let type = 'other'
      if (data.includes('joined') || data.includes('left')) {
        type = 'system'
      } else if (data.startsWith(username + ':')) {
        type = 'self'
      }

      setMessages((prev) => [...prev, { text: data, type }])
    }

    ws.onclose = () => setConnected(false)
  }, [ws, username])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = () => {
    const msg = input.trim()
    if (!msg || !ws) return
    ws.send(msg)
    setInput('')
  }

  // Parse message for display
  const renderMessage = (msg, index) => {
    if (msg.type === 'system') {
      return (
        <div key={index} className="message system">
          {msg.text}
        </div>
      )
    }

    const parts = msg.text.split(': ')
    const sender = parts[0]
    const text = parts.slice(1).join(': ')

    return (
      <div key={index} className={`message ${msg.type}`}>
        <div className="sender">{msg.type === 'self' ? 'You' : sender}</div>
        {text}
      </div>
    )
  }

  return (
    <div className="chat-screen">
      <div className="chat-header">
        <h2>ChatWave</h2>
        <span className={`status ${connected ? '' : 'disconnected'}`}>
          ● {connected ? 'Connected' : 'Disconnected'}
        </span>
        <button className="logout-btn" onClick={onLogout}>Logout</button>
      </div>

      <div className="messages">
        {messages.map((msg, i) => renderMessage(msg, i))}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input">
        <input
          type="text"
          placeholder="Type a message"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          autoComplete="off"
        />
        <button onClick={sendMessage}>➤</button>
      </div>
    </div>
  )
}
