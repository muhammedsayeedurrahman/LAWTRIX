/**
 * Question Engine
 *
 * Manages the conversational flow of questions based on form schema
 * and user answers. Implements progressive disclosure.
 */

import { FormField, shouldAskField } from './form-schema-parser'

export interface QuestionProgress {
  answered: number
  total: number
  percentage: number
}

export class QuestionEngine {
  /**
   * Get the next unanswered question that should be asked
   */
  getNextQuestion(
    fields: FormField[],
    answers: Record<string, any>
  ): FormField | null {
    for (const field of fields) {
      // Skip if already answered
      if (answers[field.id] !== undefined) continue

      // Skip if dependencies not met
      if (!shouldAskField(field, answers)) continue

      // This is the next question to ask
      return field
    }

    return null // All questions answered
  }

  /**
   * Get progress through the form
   */
  getProgress(
    fields: FormField[],
    answers: Record<string, any>
  ): QuestionProgress {
    // Count only fields that should be asked
    const relevantFields = fields.filter(f => shouldAskField(f, answers))
    const answeredFields = relevantFields.filter(f => answers[f.id] !== undefined)

    const total = relevantFields.length
    const answered = answeredFields.length
    const percentage = total > 0 ? Math.round((answered / total) * 100) : 0

    return { answered, total, percentage }
  }

  /**
   * Check if all required questions have been answered
   */
  isComplete(
    fields: FormField[],
    answers: Record<string, any>
  ): boolean {
    const nextQuestion = this.getNextQuestion(fields, answers)
    return nextQuestion === null
  }

  /**
   * Get all unanswered questions
   */
  getUnansweredQuestions(
    fields: FormField[],
    answers: Record<string, any>
  ): FormField[] {
    return fields.filter(field =>
      answers[field.id] === undefined && shouldAskField(field, answers)
    )
  }

  /**
   * Get a specific field by ID
   */
  getField(fields: FormField[], fieldId: string): FormField | null {
    return fields.find(f => f.id === fieldId) || null
  }

  /**
   * Get summary of all answers
   */
  getAnswerSummary(
    fields: FormField[],
    answers: Record<string, any>
  ): Array<{ field: FormField; value: any }> {
    return fields
      .filter(f => answers[f.id] !== undefined)
      .map(field => ({ field, value: answers[field.id] }))
  }
}

/**
 * Singleton instance
 */
let engineInstance: QuestionEngine | null = null

export function getQuestionEngine(): QuestionEngine {
  if (!engineInstance) {
    engineInstance = new QuestionEngine()
  }
  return engineInstance
}
