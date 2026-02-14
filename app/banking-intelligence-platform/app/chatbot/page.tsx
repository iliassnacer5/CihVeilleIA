'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Send, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  timestamp: Date
}

const bankingPrompts = [
  'What are the latest capital adequacy requirements?',
  'Explain the implications of Basel IV for our institution',
  'Summarize recent regulatory updates',
  'What are the key credit risk factors this month?',
  'How does the current market volatility affect our strategy?',
]

function CollapsibleSources({ sources }: { sources: string[] }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="mt-3 pt-2 border-t border-border/40">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-xs font-semibold opacity-80 hover:opacity-100 transition-opacity focus:outline-none"
      >
        <div className={`transform transition-transform duration-200 ${isOpen ? 'rotate-90' : ''}`}>
          ▶
        </div>
        <span>{sources.length} Sources {isOpen ? '(Hide)' : '(Show)'}</span>
      </button>

      {isOpen && (
        <ul className="mt-2 space-y-1 animate-in fade-in slide-in-from-top-1 duration-200">
          {sources.map((source, idx) => (
            <li key={idx} className="text-xs opacity-75 flex items-start gap-2 pl-4">
              <span className="block mt-1 text-[10px]">•</span>
              <a
                href={source.startsWith('http') ? source : '#'}
                target={source.startsWith('http') ? '_blank' : undefined}
                rel="noopener noreferrer"
                className={source.startsWith('http') ? 'hover:underline text-accent' : ''}
              >
                {source}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function ChatbotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: 'assistant',
      content:
        'Hello! I am your AI banking intelligence assistant. I can help you understand regulatory updates, market conditions, credit risks, and more. Ask me any question about our monitored sources and documents.',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    const text = input.trim()
    if (!text) return

    const userMessage: Message = {
      id: messages.length + 1,
      role: 'user',
      content: text,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const data = await api.askChatbot(text)
      const assistantMessage: Message = {
        id: messages.length + 2,
        role: 'assistant',
        content: data.answer,
        sources: data.sources.map((s: any) => s.title || s.url),
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chatbot error:', error)
      const errorMessage: Message = {
        id: messages.length + 2,
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Please try again later.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handlePromptClick = (prompt: string) => {
    setInput(prompt)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-160px)] max-w-4xl mx-auto">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-6 p-4 border border-border rounded-lg bg-card">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-2xl rounded-lg p-4 ${message.role === 'user'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-foreground border border-border'
                }`}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>

              {message.sources && message.sources.length > 0 && (
                <CollapsibleSources sources={message.sources} />
              )}

              <p className="text-xs opacity-70 mt-2">
                {message.timestamp.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-secondary text-foreground border border-border rounded-lg p-4">
              <div className="flex gap-2">
                <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce delay-100" />
                <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts */}
      {messages.length === 1 && (
        <div className="mb-6 space-y-3">
          <p className="text-sm font-semibold text-foreground">
            Banking-oriented prompts to get started:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {bankingPrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handlePromptClick(prompt)}
                className="flex items-start gap-3 p-3 rounded-lg border border-border hover:bg-secondary transition-colors text-left"
              >
                <Zap size={16} className="text-accent mt-0.5 flex-shrink-0" />
                <span className="text-sm text-foreground">{prompt}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-border pt-4">
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about regulatory updates, credit risk, market conditions..."
            className="flex-1 px-4 py-3 border border-border rounded-lg bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-none max-h-24"
            rows={1}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!input.trim() || isLoading}
            className="self-end"
          >
            <Send size={18} />
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          AI responses are based on collected documents. Sources are cited for
          transparency.
        </p>
      </div>
    </div>
  )
}
