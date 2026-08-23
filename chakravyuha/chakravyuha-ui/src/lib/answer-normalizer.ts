/**
 * Answer Normalizer
 *
 * Interprets natural language answers and converts them to typed values.
 * Handles multiple languages (English + Hindi).
 */

/**
 * Normalize a boolean answer from natural language
 */
export function normalizeBoolean(input: string): boolean | null {
  const normalized = input.toLowerCase().trim()

  // English affirmative
  const yesPatterns = ['yes', 'yeah', 'yep', 'yup', 'sure', 'ok', 'okay', 'true', 'correct', 'right', 'affirmative']
  if (yesPatterns.some(p => normalized.includes(p))) return true

  // Hindi affirmative
  const hindiYes = ['हां', 'हाँ', 'जी', 'ठीक', 'सही', 'bilkul', 'ha', 'haan', 'ji', 'theek', 'sahi']
  if (hindiYes.some(p => normalized.includes(p))) return true

  // English negative
  const noPatterns = ['no', 'nope', 'nah', 'not', 'false', 'wrong', 'negative', 'never']
  if (noPatterns.some(p => normalized.includes(p))) return true

  // Hindi negative
  const hindiNo = ['नहीं', 'ना', 'गलत', 'nahi', 'naa', 'galat']
  if (hindiNo.some(p => normalized.includes(p))) return false

  return null // Could not determine
}

/**
 * Normalize a number answer from natural language
 */
export function normalizeNumber(input: string): number | null {
  const normalized = input.toLowerCase().trim()

  // Extract numeric digits
  const digits = normalized.match(/\d+(?:\.\d+)?/)
  if (digits) {
    const baseNumber = parseFloat(digits[0])

    // Check for multipliers
    if (normalized.includes('thousand') || normalized.includes('हजार') || normalized.includes('k')) {
      return baseNumber * 1000
    }
    if (normalized.includes('lakh') || normalized.includes('लाख')) {
      return baseNumber * 100000
    }
    if (normalized.includes('crore') || normalized.includes('करोड़')) {
      return baseNumber * 10000000
    }
    if (normalized.includes('million') || normalized.includes('m')) {
      return baseNumber * 1000000
    }

    return baseNumber
  }

  // Try to parse number words (basic)
  const numberWords: Record<string, number> = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
    'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
    'eighty': 80, 'ninety': 90, 'hundred': 100
  }

  for (const [word, value] of Object.entries(numberWords)) {
    if (normalized === word) return value
  }

  return null
}

/**
 * Normalize a select/choice answer using fuzzy matching
 */
export function normalizeSelect(input: string, options: string[]): string | null {
  const normalized = input.toLowerCase().trim()

  // Exact match (case-insensitive)
  const exactMatch = options.find(opt => opt.toLowerCase() === normalized)
  if (exactMatch) return exactMatch

  // Partial match (input contains option or option contains input)
  const partialMatch = options.find(opt => {
    const optLower = opt.toLowerCase()
    return optLower.includes(normalized) || normalized.includes(optLower)
  })
  if (partialMatch) return partialMatch

  // Fuzzy match based on first few characters
  const fuzzyMatch = options.find(opt => {
    const optLower = opt.toLowerCase()
    const minLength = Math.min(3, normalized.length)
    return optLower.substring(0, minLength) === normalized.substring(0, minLength)
  })
  if (fuzzyMatch) return fuzzyMatch

  return null
}

/**
 * Normalize a date answer
 */
export function normalizeDate(input: string): Date | null {
  const normalized = input.trim()

  // Try standard date formats
  const date = new Date(normalized)
  if (!isNaN(date.getTime())) return date

  // Handle relative dates
  const today = new Date()

  if (normalized.includes('today')) return today

  if (normalized.includes('yesterday')) {
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    return yesterday
  }

  if (normalized.includes('tomorrow')) {
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    return tomorrow
  }

  // Extract year if present
  const yearMatch = normalized.match(/\b(19|20)\d{2}\b/)
  if (yearMatch) {
    return new Date(parseInt(yearMatch[0]), 0, 1)
  }

  return null
}

/**
 * Main answer normalizer - routes to appropriate function
 */
export function normalizeAnswer(
  rawInput: string,
  fieldType: 'text' | 'number' | 'boolean' | 'select' | 'date',
  options?: string[]
): any {
  const trimmed = rawInput.trim()
  if (!trimmed) return null

  switch (fieldType) {
    case 'boolean':
      return normalizeBoolean(trimmed)

    case 'number':
      return normalizeNumber(trimmed)

    case 'select':
      return options ? normalizeSelect(trimmed, options) : null

    case 'date':
      return normalizeDate(trimmed)

    case 'text':
    default:
      return trimmed
  }
}

/**
 * Format an answer for display
 */
export function formatAnswer(value: any, fieldType: string): string {
  if (value === null || value === undefined) return '—'

  switch (fieldType) {
    case 'boolean':
      return value ? 'Yes' : 'No'

    case 'number':
      return value.toLocaleString('en-IN')

    case 'date':
      return value instanceof Date ? value.toLocaleDateString('en-IN') : String(value)

    default:
      return String(value)
  }
}
