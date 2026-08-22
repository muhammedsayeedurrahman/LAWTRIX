/**
 * Next.js Middleware for i18n routing
 * Detects user's preferred language and redirects accordingly
 */

import createMiddleware from 'next-intl/middleware';
import { locales, defaultLocale } from './i18n.config';

export default createMiddleware({
  // All supported locales
  locales,

  // Default locale
  defaultLocale,

  // Locale detection strategy
  localeDetection: true,

  // Locale prefix strategy (always show locale in URL)
  localePrefix: 'always',
});

export const config = {
  // Match all pathnames except for
  // - /api (API routes)
  // - /_next (Next.js internals)
  // - /favicon.ico, /sitemap.xml, /robots.txt (static files)
  matcher: ['/((?!api|_next|favicon.ico|sitemap.xml|robots.txt).*)'],
};
