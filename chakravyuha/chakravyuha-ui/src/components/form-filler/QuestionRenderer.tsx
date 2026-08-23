"use client"

import { useState } from 'react'
import { FormField } from '@/lib/form-schema-parser'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Check, X } from 'lucide-react'

interface QuestionRendererProps {
  field: FormField
  onAnswer: (value: any) => void
  disabled?: boolean
}

export function QuestionRenderer({ field, onAnswer, disabled }: QuestionRendererProps) {
  const [textValue, setTextValue] = useState('')

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault()
    if (textValue.trim()) {
      onAnswer(textValue.trim())
      setTextValue('')
    }
  }

  if (field.type === 'boolean') {
    return (
      <div className="flex flex-col gap-3">
        <Label className="text-sm font-medium">{field.label}</Label>
        {field.helpText && (
          <p className="text-xs text-muted-foreground">{field.helpText}</p>
        )}
        <div className="flex gap-2">
          <Button
            onClick={() => onAnswer(true)}
            disabled={disabled}
            variant="outline"
            className="flex-1"
          >
            <Check className="w-4 h-4 mr-2" />
            Yes
          </Button>
          <Button
            onClick={() => onAnswer(false)}
            disabled={disabled}
            variant="outline"
            className="flex-1"
          >
            <X className="w-4 h-4 mr-2" />
            No
          </Button>
        </div>
      </div>
    )
  }

  if (field.type === 'select' && field.options) {
    return (
      <div className="flex flex-col gap-3">
        <Label className="text-sm font-medium">{field.label}</Label>
        {field.helpText && (
          <p className="text-xs text-muted-foreground">{field.helpText}</p>
        )}
        <Select onValueChange={onAnswer} disabled={disabled}>
          <SelectTrigger>
            <SelectValue placeholder="Select an option..." />
          </SelectTrigger>
          <SelectContent>
            {field.options.map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    )
  }

  if (field.type === 'number') {
    return (
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <Label className="text-sm font-medium">{field.label}</Label>
        {field.helpText && (
          <p className="text-xs text-muted-foreground">{field.helpText}</p>
        )}
        <div className="flex gap-2">
          <Input
            type="number"
            value={textValue}
            onChange={(e) => setTextValue(e.target.value)}
            placeholder={field.min !== undefined ? `Min: ${field.min}` : 'Enter a number...'}
            min={field.min}
            max={field.max}
            disabled={disabled}
            className="flex-1"
          />
          <Button type="submit" disabled={disabled || !textValue.trim()}>
            Send
          </Button>
        </div>
      </form>
    )
  }

  // Default: text input
  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <Label className="text-sm font-medium">{field.label}</Label>
      {field.helpText && (
        <p className="text-xs text-muted-foreground">{field.helpText}</p>
      )}
      <div className="flex gap-2">
        <Input
          type="text"
          value={textValue}
          onChange={(e) => setTextValue(e.target.value)}
          placeholder="Type your answer..."
          disabled={disabled}
          className="flex-1"
        />
        <Button type="submit" disabled={disabled || !textValue.trim()}>
          Send
        </Button>
      </div>
    </form>
  )
}
