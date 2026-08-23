"use client"

import { useState, useEffect, useRef } from 'react'
import { FormField, parseSchemeToFormFields, validateAnswer } from '@/lib/form-schema-parser'
import { getQuestionEngine } from '@/lib/question-engine'
import { normalizeAnswer } from '@/lib/answer-normalizer'
import { ChatBubble, ChatMessage } from './ChatBubble'
import { QuestionRenderer } from './QuestionRenderer'
import { FormPreview } from './FormPreview'
import { ProgressIndicator } from './ProgressIndicator'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Loader2, Send } from 'lucide-react'

interface ChatFormFillerProps {
  schemeId: string
  schemeName: string
  onComplete: (answers: Record<string, any>) => void
  onCancel?: () => void
}

type FormState = 'greeting' | 'asking' | 'complete'

export function ChatFormFiller({ schemeId, schemeName, onComplete, onCancel }: ChatFormFillerProps) {
  const [state, setState] = useState<FormState>('greeting')
  const [fields, setFields] = useState<FormField[]>([])
  const [answers, setAnswers] = useState<Record<string, any>>({})
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [currentField, setCurrentField] = useState<FormField | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const engine = getQuestionEngine()

  // Initialize form fields
  useEffect(() => {
    const formFields = parseSchemeToFormFields({ id: schemeId, name: schemeName })
    setFields(formFields)

    // Add greeting message
    setMessages([
      {
        role: 'assistant',
        content: `Hi! I'll help you check your eligibility for ${schemeName}. I'll ask you a few questions. Let's get started!`,
        timestamp: new Date()
      }
    ])

    // Start with first question
    setState('asking')
  }, [schemeId, schemeName])

  // Get next question when state changes
  useEffect(() => {
    if (state === 'asking' && fields.length > 0) {
      const nextQuestion = engine.getNextQuestion(fields, answers)

      if (nextQuestion) {
        setCurrentField(nextQuestion)
        // Add question as assistant message
        setTimeout(() => {
          setMessages(prev => [
            ...prev,
            {
              role: 'assistant',
              content: nextQuestion.label + (nextQuestion.helpText ? `\n\n${nextQuestion.helpText}` : ''),
              timestamp: new Date()
            }
          ])
        }, 300)
      } else {
        // All questions answered
        setState('complete')
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: `Great! I have all the information I need. You can review your answers below and submit when ready.`,
            timestamp: new Date()
          }
        ])
      }
    }
  }, [state, fields, answers, engine])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleAnswer = async (rawValue: any) => {
    if (!currentField || isProcessing) return

    setIsProcessing(true)

    // Normalize the answer based on field type
    const normalizedValue = typeof rawValue === 'string'
      ? normalizeAnswer(rawValue, currentField.type, currentField.options)
      : rawValue

    // Validate the answer
    const validation = validateAnswer(currentField, normalizedValue)

    if (!validation.valid) {
      // Show error message
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ ${validation.error || 'Invalid answer'}. Please try again.`,
          timestamp: new Date()
        }
      ])
      setIsProcessing(false)
      return
    }

    // Add user's answer to messages
    const displayValue = currentField.type === 'boolean'
      ? (normalizedValue ? 'Yes' : 'No')
      : String(normalizedValue)

    setMessages(prev => [
      ...prev,
      {
        role: 'user',
        content: displayValue,
        timestamp: new Date()
      }
    ])

    // Save answer
    setAnswers(prev => ({
      ...prev,
      [currentField.id]: normalizedValue
    }))

    // Small delay before next question
    await new Promise(resolve => setTimeout(resolve, 500))
    setIsProcessing(false)
  }

  const handleEdit = (fieldId: string) => {
    const field = fields.find(f => f.id === fieldId)
    if (field) {
      // Remove this answer and all dependent answers
      setAnswers(prev => {
        const newAnswers = { ...prev }
        delete newAnswers[fieldId]

        // Remove dependent answers
        fields.forEach(f => {
          if (f.dependsOn?.field === fieldId) {
            delete newAnswers[f.id]
          }
        })

        return newAnswers
      })

      // Go back to asking state
      setState('asking')

      // Add message about editing
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `Let's update that answer. ${field.label}`,
          timestamp: new Date()
        }
      ])
    }
  }

  const handleSubmit = () => {
    onComplete(answers)
  }

  const progress = engine.getProgress(fields, answers)

  return (
    <div className="flex flex-col h-full max-w-5xl mx-auto gap-4">
      {/* Header with Progress */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-2">
            <h2 className="text-lg font-semibold">{schemeName}</h2>
            <ProgressIndicator progress={progress} />
          </div>
        </CardContent>
      </Card>

      <div className="flex-1 flex gap-4 min-h-0">
        {/* Chat Area */}
        <Card className="flex-1 flex flex-col">
          <CardContent className="flex-1 flex flex-col p-4 min-h-0">
            {/* Messages */}
            <ScrollArea className="flex-1 pr-4" ref={scrollRef}>
              <div className="space-y-4">
                {messages.map((msg, idx) => (
                  <ChatBubble key={idx} message={msg} />
                ))}
                {isProcessing && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Processing...</span>
                  </div>
                )}
              </div>
            </ScrollArea>

            {/* Question Input */}
            {currentField && state === 'asking' && (
              <div className="mt-4 pt-4 border-t">
                <QuestionRenderer
                  field={currentField}
                  onAnswer={handleAnswer}
                  disabled={isProcessing}
                />
              </div>
            )}

            {/* Complete State Actions */}
            {state === 'complete' && (
              <div className="mt-4 pt-4 border-t flex gap-2">
                <Button onClick={handleSubmit} className="flex-1">
                  <Send className="w-4 h-4 mr-2" />
                  Check Eligibility
                </Button>
                {onCancel && (
                  <Button onClick={onCancel} variant="outline">
                    Cancel
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Form Preview Sidebar */}
        <FormPreview
          fields={fields}
          answers={answers}
          onEdit={handleEdit}
          className="w-80 hidden md:block"
        />
      </div>
    </div>
  )
}
