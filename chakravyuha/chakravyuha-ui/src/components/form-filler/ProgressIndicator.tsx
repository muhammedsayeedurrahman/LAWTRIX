"use client"

import { QuestionProgress } from '@/lib/question-engine'
import { Progress } from '@/components/ui/progress'

interface ProgressIndicatorProps {
  progress: QuestionProgress
}

export function ProgressIndicator({ progress }: ProgressIndicatorProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Progress</span>
        <span className="font-semibold text-primary">
          {progress.answered}/{progress.total} questions
        </span>
      </div>
      <Progress value={progress.percentage} className="h-2" />
      {progress.percentage === 100 && (
        <p className="text-xs text-primary font-medium">
          ✓ All questions answered!
        </p>
      )}
    </div>
  )
}
