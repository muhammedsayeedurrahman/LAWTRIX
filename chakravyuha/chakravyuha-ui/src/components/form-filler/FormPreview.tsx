"use client"

import { FormField } from '@/lib/form-schema-parser'
import { formatAnswer } from '@/lib/answer-normalizer'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Edit2, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FormPreviewProps {
  fields: FormField[]
  answers: Record<string, any>
  onEdit?: (fieldId: string) => void
  className?: string
}

export function FormPreview({ fields, answers, onEdit, className }: FormPreviewProps) {
  const answeredFields = fields.filter(f => answers[f.id] !== undefined)
  const totalRequired = fields.filter(f => f.required).length
  const answeredRequired = answeredFields.filter(f => f.required).length

  return (
    <Card className={cn('', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Your Answers</CardTitle>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <CheckCircle2 className="w-4 h-4 text-primary" />
            <span>
              {answeredRequired}/{totalRequired} required
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {answeredFields.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            No answers yet. Start answering questions above.
          </p>
        ) : (
          answeredFields.map((field) => (
            <div
              key={field.id}
              className="flex items-start justify-between gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
            >
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-muted-foreground mb-1">
                  {field.label}
                </p>
                <p className="text-sm font-semibold truncate">
                  {formatAnswer(answers[field.id], field.type)}
                </p>
              </div>
              {onEdit && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onEdit(field.id)}
                  className="flex-shrink-0 h-8 w-8 p-0"
                >
                  <Edit2 className="w-3 h-3" />
                </Button>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}
