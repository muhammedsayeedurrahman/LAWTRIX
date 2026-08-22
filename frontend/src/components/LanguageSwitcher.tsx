/**
 * Language Switcher Component
 * Allows users to switch between 9 supported languages
 */

'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useRouter, usePathname } from 'next/navigation';
import { useState, useRef, useEffect } from 'react';
import { locales, localeNames, type Locale } from '../../i18n.config';

export default function LanguageSwitcher() {
  const t = useTranslations('language');
  const locale = useLocale() as Locale;
  const router = useRouter();
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLanguageChange = (newLocale: Locale) => {
    // Store preference in localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('preferred-locale', newLocale);
    }

    // Navigate to new locale
    const segments = pathname.split('/');
    segments[1] = newLocale;
    router.push(segments.join('/'));

    setIsOpen(false);
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent, newLocale?: Locale) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (newLocale) {
        handleLanguageChange(newLocale);
      } else {
        setIsOpen(!isOpen);
      }
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={(e) => handleKeyDown(e)}
        className="flex items-center gap-2 px-4 py-2 text-white bg-transparent hover:bg-white/10 rounded-lg transition-colors"
        aria-expanded={isOpen}
        aria-haspopup="true"
        aria-label={t('selectLanguage')}
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
          />
        </svg>
        <span className="hidden sm:inline">{locale.toUpperCase()}</span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
          <div className="px-4 py-2 text-sm font-medium text-gray-500 border-b border-gray-100">
            {t('selectLanguage')}
          </div>

          {locales.map((loc) => (
            <button
              key={loc}
              onClick={() => handleLanguageChange(loc)}
              onKeyDown={(e) => handleKeyDown(e, loc)}
              className={`w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center justify-between transition-colors ${
                locale === loc ? 'bg-lawtrix-blue text-white hover:bg-lawtrix-blue' : 'text-gray-900'
              }`}
              role="menuitem"
            >
              <span className="text-base">{localeNames[loc]}</span>
              {locale === loc && (
                <svg
                  className="w-5 h-5 text-success-green"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
