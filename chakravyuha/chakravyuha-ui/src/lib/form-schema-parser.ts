/**
 * Form Schema Parser
 *
 * Converts scheme eligibility schemas into conversational question flows.
 */

export interface FormField {
  id: string
  label: string
  type: 'text' | 'number' | 'boolean' | 'select' | 'date'
  required: boolean
  options?: string[]
  dependsOn?: {
    field: string
    value: any
  }
  helpText?: string
  validationPattern?: string
  min?: number
  max?: number
}

export interface FormSchema {
  id: string
  name: string
  fields: FormField[]
}

/**
 * Parse a scheme's eligibility schema into form fields
 */
export function parseSchemeToFormFields(scheme: {
  id: string
  name: string
  eligibility_criteria?: Record<string, any>
}): FormField[] {
  const fields: FormField[] = []

  // Common profile fields for all schemes
  const commonFields: FormField[] = [
    {
      id: 'age',
      label: 'What is your age?',
      type: 'number',
      required: true,
      min: 0,
      max: 120,
      helpText: 'Your age in years'
    },
    {
      id: 'is_indian_citizen',
      label: 'Are you an Indian citizen?',
      type: 'boolean',
      required: true,
    },
    {
      id: 'state',
      label: 'Which state do you live in?',
      type: 'select',
      required: true,
      options: [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
        'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
        'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
        'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
        'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
        'Delhi', 'Puducherry', 'Jammu and Kashmir', 'Ladakh'
      ]
    }
  ]

  // Scheme-specific fields based on ID
  const schemeSpecificFields = getSchemeSpecificFields(scheme.id)

  return [...commonFields, ...schemeSpecificFields]
}

/**
 * Get scheme-specific form fields
 */
function getSchemeSpecificFields(schemeId: string): FormField[] {
  const schemeFieldMap: Record<string, FormField[]> = {
    'pm-jay': [
      {
        id: 'listed_in_secc_2011_or_state_database',
        label: 'Are you listed in SECC 2011 or state health database?',
        type: 'boolean',
        required: true,
        helpText: 'PM-JAY covers families in SECC 2011 database'
      },
      {
        id: 'annual_family_income',
        label: 'What is your annual family income (in rupees)?',
        type: 'number',
        required: false,
        helpText: 'Optional - helps determine eligibility'
      }
    ],
    'pm-kisan': [
      {
        id: 'owns_cultivable_land',
        label: 'Do you own cultivable land?',
        type: 'boolean',
        required: true,
      },
      {
        id: 'landholding_hectares',
        label: 'How much land do you own (in hectares)?',
        type: 'number',
        required: true,
        dependsOn: { field: 'owns_cultivable_land', value: true },
        min: 0.01,
        helpText: 'All farmer families are eligible regardless of landholding size'
      },
      {
        id: 'is_institutional_landowner',
        label: 'Is the land owned by an institution or government?',
        type: 'boolean',
        required: true,
        dependsOn: { field: 'owns_cultivable_land', value: true }
      }
    ],
    'pm-ujjvala': [
      {
        id: 'is_female_applicant',
        label: 'Is the applicant female (woman of the household)?',
        type: 'boolean',
        required: true,
        helpText: 'PM-Ujjvala requires female applicant'
      },
      {
        id: 'belongs_to_eligible_category',
        label: 'Do you belong to BPL/SC/ST/PMAY/AAY category?',
        type: 'boolean',
        required: true,
        dependsOn: { field: 'is_female_applicant', value: true }
      },
      {
        id: 'already_has_lpg_connection',
        label: 'Do you already have an LPG connection in your household?',
        type: 'boolean',
        required: true,
        dependsOn: { field: 'is_female_applicant', value: true }
      }
    ],
    'nsap-old-age': [
      {
        id: 'is_bpl',
        label: 'Do you belong to a Below Poverty Line (BPL) family?',
        type: 'boolean',
        required: true,
        helpText: 'BPL status is required for NSAP'
      },
      {
        id: 'has_regular_income_source',
        label: 'Do you have any regular source of income?',
        type: 'boolean',
        required: true,
        helpText: 'Pension is for destitute persons without income'
      }
    ],
    'sukanya-samriddhi': [
      {
        id: 'is_girl_child',
        label: 'Is this for a girl child?',
        type: 'boolean',
        required: true,
      },
      {
        id: 'girl_child_age',
        label: 'What is the age of the girl child?',
        type: 'number',
        required: true,
        dependsOn: { field: 'is_girl_child', value: true },
        min: 0,
        max: 10,
        helpText: 'Account can be opened until the girl child attains age of 10 years'
      },
      {
        id: 'existing_ssy_accounts_count',
        label: 'How many existing SSY accounts does the family have?',
        type: 'number',
        required: true,
        dependsOn: { field: 'is_girl_child', value: true },
        min: 0,
        max: 10,
        helpText: 'Maximum 2 accounts per family allowed'
      }
    ]
  }

  return schemeFieldMap[schemeId] || []
}

/**
 * Check if a field should be asked based on current answers
 */
export function shouldAskField(
  field: FormField,
  answers: Record<string, any>
): boolean {
  if (!field.dependsOn) return true

  const dependentValue = answers[field.dependsOn.field]
  return dependentValue === field.dependsOn.value
}

/**
 * Validate an answer against field constraints
 */
export function validateAnswer(
  field: FormField,
  value: any
): { valid: boolean; error?: string } {
  if (field.required && (value === undefined || value === null || value === '')) {
    return { valid: false, error: 'This field is required' }
  }

  if (field.type === 'number') {
    const num = Number(value)
    if (isNaN(num)) {
      return { valid: false, error: 'Please enter a valid number' }
    }
    if (field.min !== undefined && num < field.min) {
      return { valid: false, error: `Value must be at least ${field.min}` }
    }
    if (field.max !== undefined && num > field.max) {
      return { valid: false, error: `Value must be at most ${field.max}` }
    }
  }

  if (field.type === 'select' && field.options) {
    if (!field.options.includes(value)) {
      return { valid: false, error: 'Please select a valid option' }
    }
  }

  return { valid: true }
}
