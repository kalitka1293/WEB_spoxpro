import React, { useState, useCallback } from 'react'

interface ToastMessage {
  id: number;
  text: string;
  type: 'success' | 'error';
}

let addToast: (text: string, type?: 'success' | 'error') => void = () => {}

export const toast = (text: string, type: 'success' | 'error' = 'error') => addToast(text, type)

const Toast: React.FC = () => {
  const [messages, setMessages] = useState<ToastMessage[]>([])

  addToast = useCallback((text: string, type: 'success' | 'error' = 'error') => {
    const id = Date.now()
    setMessages(prev => [...prev, { id, text, type }])
    setTimeout(() => setMessages(prev => prev.filter(m => m.id !== id)), 3000)
  }, [])

  if (messages.length === 0) return null

  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[9999] space-y-2">
      {messages.map(m => (
        <div
          key={m.id}
          className={`px-4 py-3 rounded-lg shadow-lg text-white text-sm animate-fade-in ${m.type === 'success' ? 'bg-green-600' : 'bg-red-600'}`}
        >
          {m.text}
        </div>
      ))}
    </div>
  )
}

export default Toast
