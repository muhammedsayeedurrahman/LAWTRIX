/**
 * i18n Configuration for LAWTRIX
 * Supports 9 Indian languages as per Phase 1 requirements
 */

export const locales = [
  'en',    // English
  'hi',    // Hindi
  'bn',    // Bengali
  'ta',    // Tamil
  'te',    // Telugu
  'mr',    // Marathi
  'gu',    // Gujarati
  'kn',    // Kannada
  'ml',    // Malayalam
  'pa',    // Punjabi
] as const;

export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = 'en';

export const localeNames: Record<Locale, string> = {
  en: 'English',
  hi: 'हिंदी',
  bn: 'বাংলা',
  ta: 'தமிழ்',
  te: 'తెలుగు',
  mr: 'मराठी',
  gu: 'ગુજરાતી',
  kn: 'ಕನ್ನಡ',
  ml: 'മലയാളം',
  pa: 'ਪੰਜਾਬੀ',
};

export const localeNativeName: Record<Locale, string> = {
  en: 'English',
  hi: 'Hindi',
  bn: 'Bengali',
  ta: 'Tamil',
  te: 'Telugu',
  mr: 'Marathi',
  gu: 'Gujarati',
  kn: 'Kannada',
  ml: 'Malayalam',
  pa: 'Punjabi',
};

// RTL support (currently none of our supported languages are RTL)
export const rtlLocales: Locale[] = [];

export const isRTL = (locale: Locale): boolean => {
  return rtlLocales.includes(locale);
};
