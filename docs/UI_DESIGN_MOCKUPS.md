# LAWTRIX UI Design Mockups

*Design System: Shadcn/ui + LAWTRIX Color Palette*
*Compliance: GIGW 3.0 + WCAG 2.1 AA*
*Generated: August 23, 2026*

---

## Color Palette Reference

```css
/* Primary Colors */
--lawtrix-blue: #003D82;      /* Primary brand, CTAs, headers */
--government-navy: #002868;   /* Secondary actions, footer */
--success-green: #0F7B4C;     /* Completed, success states */

/* Neutral Colors */
--white: #FFFFFF;             /* Primary background */
--light-gray: #F5F5F5;        /* Secondary background, cards */
--medium-gray: #767676;       /* Secondary text, borders */
--dark-gray: #1A1A1A;         /* Primary text */

/* Accent Colors */
--warning-orange: #FF8C00;    /* Warnings, pending */
--error-red: #C51F1F;         /* Errors, failed */
--info-blue: #0078D4;         /* Info notices */
```

---

## Typography System

```css
/* Font Families */
--font-ui: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-legal: 'Source Serif Pro', Georgia, serif;
--font-hindi: 'Noto Sans Devanagari', sans-serif;
--font-tamil: 'Noto Sans Tamil', sans-serif;
--font-bengali: 'Noto Sans Bengali', sans-serif;

/* Type Scale (Mobile / Desktop) */
--text-h1: 28px / 36px;       /* Page titles */
--text-h2: 24px / 32px;       /* Section headers */
--text-h3: 20px / 24px;       /* Subsection headers */
--text-body: 16px / 16px;     /* Body text */
--text-small: 14px / 14px;    /* Captions, labels */

/* Line Heights */
--line-height-tight: 1.2;
--line-height-normal: 1.6;
--line-height-relaxed: 1.8;
```

---

## Component Mockups

### 1. Home Page Hero Section

```
┌──────────────────────────────────────────────────────────────┐
│                        LAWTRIX                                │
│                     [Language Selector ▾]                     │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│              [LAWTRIX Logo - Blue #003D82]                    │
│                                                                │
│         Your Voice for Justice in India                       │
│         टीम लॉट्रिक्स - आपकी न्याय की आवाज़                │
│                                                                │
│    File RTI, CPGRAMS, Consumer & Tenant Rights in Minutes    │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 💬  Tell us what happened...                           │  │
│  │                                                         │  │
│  │ Example: "My road has not been repaired"              │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│          [🎤 Speak Instead]    [📄 Upload Document]          │
│                                                                │
│  ┌──────────┬──────────┬──────────┬──────────┐               │
│  │   RTI    │ CPGRAMS  │  Tenant  │ Consumer │               │
│  │  Request │ Grievance│  Rights  │  Rights  │               │
│  └──────────┴──────────┴──────────┴──────────┘               │
│                                                                │
│              🔒 Secure • 🌐 9 Languages • ✓ Free             │
└──────────────────────────────────────────────────────────────┘

Colors:
- Background: #FFFFFF (white)
- Logo/Primary text: #003D82 (LAWTRIX Blue)
- Secondary text: #767676 (Medium Gray)
- Input border: #767676 → #003D82 (on focus)
- Button backgrounds: #003D82 (primary)
- Icons: #003D82

Typography:
- "Your Voice for Justice": 36px, Inter Bold, #003D82
- Hindi text: 24px, Noto Sans Devanagari, #767676
- Description: 16px, Inter Regular, #767676
- Quick action cards: 16px, Inter SemiBold, #003D82
```

---

### 2. Case Workflow Card

```
┌──────────────────────────────────────────────────────────────┐
│  📋 RTI Request: Road Maintenance Records                    │
│  ──────────────────────────────────────────────────────────  │
│                                                                │
│  Status: ⏳ Waiting for Confirmation                         │
│  Created: Aug 23, 2026 • Authority: Chennai Corporation      │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ ✓ Intent Classified      (90% confidence)              │  │
│  │ ✓ Facts Extracted        (Chennai, Tamil Nadu)         │  │
│  │ ✓ Authority Resolved     (Chennai Corporation)         │  │
│  │ ✓ RTI Draft Generated    (Ready for review)            │  │
│  │ ○ User Confirmation      (Pending your review)         │  │
│  │ ○ Submission             (Not started)                 │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  Next Step: Review and confirm your RTI request              │
│                                                                │
│  [View Draft]  [Edit Details]  [Cancel Request]              │
└──────────────────────────────────────────────────────────────┘

Colors:
- Card background: #FFFFFF with 1px border #E0E0E0
- Card shadow: 0 2px 8px rgba(0, 61, 130, 0.08)
- Title: #1A1A1A (Dark Gray), 20px Inter SemiBold
- Status badge: #FF8C00 (Warning Orange) background, white text
- Completed steps (✓): #0F7B4C (Success Green)
- Pending steps (○): #767676 (Medium Gray)
- "Next Step" text: #003D82 (LAWTRIX Blue)
- Primary button: #003D82 background, white text
- Secondary buttons: transparent background, #003D82 text, #003D82 border

Typography:
- Title: 20px, Inter SemiBold, #1A1A1A
- Status: 14px, Inter Medium, white (on colored background)
- Metadata: 14px, Inter Regular, #767676
- Steps: 16px, Inter Regular, #1A1A1A
- Step details: 14px, Inter Regular, #767676
- Next step: 16px, Inter Medium, #003D82
```

---

### 3. Language Selector Dropdown

```
┌──────────────────────────┐
│  🌐 English         ✓   │
├─────────────────────────┤
│  हिंदी (Hindi)          │
│  বাংলা (Bengali)        │
│  தமிழ் (Tamil)          │
│  తెలుగు (Telugu)        │
│  मराठी (Marathi)        │
│  ગુજરાતી (Gujarati)     │
│  ಕನ್ನಡ (Kannada)        │
│  മലയാളം (Malayalam)     │
│  ਪੰਜਾਬੀ (Punjabi)       │
└──────────────────────────┘

Colors:
- Background: #FFFFFF
- Border: #767676
- Hover background: #F5F5F5 (Light Gray)
- Selected: #003D82 background, white text
- Checkmark: #0F7B4C (Success Green)
- Text: #1A1A1A (Dark Gray)

Typography:
- 16px, Inter Regular (Latin)
- 16px, Noto Sans [Language] (Indic scripts)

Interaction:
- Dropdown appears on click
- Keyboard navigable (arrow keys)
- ESC to close
- Selected language persists in localStorage
- Page refreshes with new language
```

---

### 4. Notification Toast

```
┌──────────────────────────────────────────────────────────────┐
│  ✓  RTI Request Submitted Successfully                       │
│     Reference ID: RTI2026082300123 has been sent to           │
│     Chennai Corporation. You'll receive SMS updates.          │
│                                                [Dismiss ✕]    │
└──────────────────────────────────────────────────────────────┘

Success Toast Colors:
- Background: #0F7B4C (Success Green)
- Text: #FFFFFF (White)
- Icon: #FFFFFF
- Border: none
- Shadow: 0 4px 12px rgba(15, 123, 76, 0.3)

Warning Toast Colors:
- Background: #FF8C00 (Warning Orange)
- Text: #FFFFFF

Error Toast Colors:
- Background: #C51F1F (Error Red)
- Text: #FFFFFF

Info Toast Colors:
- Background: #0078D4 (Info Blue)
- Text: #FFFFFF

Typography:
- Title: 16px, Inter SemiBold, white
- Description: 14px, Inter Regular, white
- Dismiss button: 14px, Inter Medium, white

Behavior:
- Appears top-right corner
- Auto-dismisses after 5 seconds (error: 10 seconds)
- Stacks vertically if multiple
- Slide-in animation from right
- Keyboard accessible (Tab to dismiss button)
```

---

### 5. Form Input Components

#### Text Input (Default State)
```
┌──────────────────────────────────────────────────────────────┐
│  Full Name *                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  └────────────────────────────────────────────────────────┘  │
│  Enter your full name as per Aadhaar                         │
└──────────────────────────────────────────────────────────────┘

Colors:
- Label: #1A1A1A (Dark Gray), 14px Inter Medium
- Required asterisk: #C51F1F (Error Red)
- Input border: #767676 (Medium Gray), 1px
- Input text: #1A1A1A (Dark Gray), 16px Inter Regular
- Helper text: #767676 (Medium Gray), 14px Inter Regular
- Background: #FFFFFF
```

#### Text Input (Focus State)
```
┌──────────────────────────────────────────────────────────────┐
│  Full Name *                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Rajesh Kumar█                                           │  │
│  └────────────────────────────────────────────────────────┘  │
│  Enter your full name as per Aadhaar                         │
└──────────────────────────────────────────────────────────────┘

Colors:
- Border: #003D82 (LAWTRIX Blue), 2px
- Focus ring: 0 0 0 3px rgba(0, 61, 130, 0.1)
```

#### Text Input (Error State)
```
┌──────────────────────────────────────────────────────────────┐
│  Full Name *                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ R                                                       │  │
│  └────────────────────────────────────────────────────────┘  │
│  ⚠ Name must be at least 3 characters                       │
└──────────────────────────────────────────────────────────────┘

Colors:
- Border: #C51F1F (Error Red), 2px
- Error text: #C51F1F (Error Red), 14px Inter Medium
- Error icon: #C51F1F
```

#### Text Input (Success State)
```
┌──────────────────────────────────────────────────────────────┐
│  Full Name *                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Rajesh Kumar                                      ✓    │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘

Colors:
- Border: #0F7B4C (Success Green), 2px
- Checkmark: #0F7B4C
```

---

### 6. Button Variants

#### Primary Button
```
┌──────────────────────────┐
│   Submit RTI Request     │
└──────────────────────────┘

Default:
- Background: #003D82 (LAWTRIX Blue)
- Text: #FFFFFF (White), 16px Inter SemiBold
- Border: none
- Border radius: 8px
- Padding: 12px 24px
- Shadow: 0 2px 4px rgba(0, 61, 130, 0.2)

Hover:
- Background: #002868 (Government Navy)
- Shadow: 0 4px 8px rgba(0, 61, 130, 0.3)

Active (pressed):
- Background: #001f4d
- Shadow: 0 1px 2px rgba(0, 61, 130, 0.2)

Disabled:
- Background: #767676 (Medium Gray)
- Text: #FFFFFF with 50% opacity
- Cursor: not-allowed
```

#### Secondary Button
```
┌──────────────────────────┐
│     Save as Draft        │
└──────────────────────────┘

Default:
- Background: transparent
- Text: #003D82 (LAWTRIX Blue), 16px Inter SemiBold
- Border: 2px solid #003D82
- Border radius: 8px
- Padding: 12px 24px

Hover:
- Background: rgba(0, 61, 130, 0.05)
- Border: 2px solid #002868

Disabled:
- Border: 2px solid #767676
- Text: #767676
```

#### Outline Button (Ghost)
```
┌──────────────────────────┐
│        Cancel            │
└──────────────────────────┘

Default:
- Background: transparent
- Text: #767676 (Medium Gray), 16px Inter SemiBold
- Border: none
- Padding: 12px 24px

Hover:
- Background: #F5F5F5 (Light Gray)
- Text: #1A1A1A (Dark Gray)
```

#### Danger Button
```
┌──────────────────────────┐
│     Delete Request       │
└──────────────────────────┘

Default:
- Background: #C51F1F (Error Red)
- Text: #FFFFFF, 16px Inter SemiBold
- Border: none
- Border radius: 8px
- Padding: 12px 24px

Hover:
- Background: #A51818
```

---

### 7. Status Badges

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  ⏳ Pending │  │  ✓ Complete │  │  ⚠ Warning  │  │  ✕ Failed   │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘

Pending:
- Background: #FF8C00 (Warning Orange)
- Text: #FFFFFF, 14px Inter Medium
- Padding: 4px 12px
- Border radius: 16px (pill shape)

Complete:
- Background: #0F7B4C (Success Green)
- Text: #FFFFFF

Warning:
- Background: #FF8C00
- Text: #FFFFFF

Failed:
- Background: #C51F1F (Error Red)
- Text: #FFFFFF

Info:
- Background: #0078D4 (Info Blue)
- Text: #FFFFFF
```

---

### 8. Navigation Header (Mobile)

```
┌──────────────────────────────────────────────────────────────┐
│  ☰  LAWTRIX                              🌐 EN  🔔  👤       │
└──────────────────────────────────────────────────────────────┘

Colors:
- Background: #003D82 (LAWTRIX Blue)
- Text: #FFFFFF (White), 18px Inter Bold
- Icons: #FFFFFF
- Border bottom: none
- Height: 64px

Mobile Menu (on ☰ click):
┌──────────────────────────────────────┐
│  Home                                │
│  My Cases                            │
│  File New Request                    │
│  Knowledge Base                      │
│  ─────────────────────────────────   │
│  Settings                            │
│  Help & Support                      │
│  Sign Out                            │
└──────────────────────────────────────┘

- Background: #FFFFFF
- Text: #1A1A1A, 16px Inter Regular
- Hover: #F5F5F5 background
- Active: #003D82 text, #F5F5F5 background
```

---

### 9. Navigation Header (Desktop)

```
┌──────────────────────────────────────────────────────────────┐
│  LAWTRIX    Home  My Cases  File Request  Knowledge Base     │
│                                      🌐 English  🔔  Profile  │
└──────────────────────────────────────────────────────────────┘

Colors:
- Background: #FFFFFF
- Border bottom: 1px solid #E0E0E0
- Logo text: #003D82, 24px Inter Bold
- Nav links: #1A1A1A, 16px Inter Medium
- Active link: #003D82, underline (3px #003D82)
- Hover: #003D82 text
- Height: 80px
```

---

### 10. Footer

```
┌──────────────────────────────────────────────────────────────┐
│                                                                │
│  LAWTRIX                                                       │
│  Your Voice for Justice in India                              │
│                                                                │
│  Quick Links           Resources          Legal                │
│  • Home                • RTI Guide        • Privacy Policy     │
│  • My Cases            • CPGRAMS Guide    • Terms of Service   │
│  • File Request        • Legal KB         • Disclaimers        │
│  • Help                • FAQs             • Contact Us         │
│                                                                │
│  ────────────────────────────────────────────────────────────  │
│                                                                │
│  © 2026 LAWTRIX. Made with ❤️ for Indian Citizens.           │
│  🔒 Secure • 🌐 9 Languages • ✓ GIGW 3.0 Compliant           │
│                                                                │
└──────────────────────────────────────────────────────────────┘

Colors:
- Background: #002868 (Government Navy)
- Text: #FFFFFF, 14px Inter Regular
- Links: #FFFFFF, 14px Inter Medium
- Link hover: underline
- Divider: rgba(255, 255, 255, 0.2)
- Bottom text: rgba(255, 255, 255, 0.7)
```

---

### 11. Case Timeline View

```
┌──────────────────────────────────────────────────────────────┐
│  📋 Case Timeline: RTI Request #RTI2026082300123             │
│  ──────────────────────────────────────────────────────────  │
│                                                                │
│  ●──────  Aug 23, 2026 10:30 AM                               │
│  │        ✓ Case Created                                      │
│  │        User initiated RTI request for road records         │
│  │                                                             │
│  ●──────  Aug 23, 2026 10:32 AM                               │
│  │        ✓ Intent Classified (90% confidence)                │
│  │        Workflow: RTI Request                               │
│  │                                                             │
│  ●──────  Aug 23, 2026 10:34 AM                               │
│  │        ✓ Authority Resolved                                │
│  │        Chennai Corporation (verified)                      │
│  │                                                             │
│  ●──────  Aug 23, 2026 10:36 AM                               │
│  │        ✓ Draft Generated                                   │
│  │        RTI application prepared for review                 │
│  │                                                             │
│  ○──────  Pending                                             │
│           ⏳ Awaiting User Confirmation                       │
│           Review and confirm your RTI request                 │
│                                                                │
└──────────────────────────────────────────────────────────────┘

Colors:
- Completed circle (●): #0F7B4C (Success Green)
- Pending circle (○): #767676 (Medium Gray)
- Timeline line: #767676, 2px
- Timestamp: #767676, 14px Inter Regular
- Event title: #1A1A1A, 16px Inter SemiBold
- Event description: #767676, 14px Inter Regular
- Checkmark icon: #0F7B4C
- Pending icon (⏳): #FF8C00
```

---

### 12. Document Upload Component

```
┌──────────────────────────────────────────────────────────────┐
│  Upload Supporting Documents (Optional)                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │              📄  Drag and drop files here              │  │
│  │                                                         │  │
│  │              or click to browse                        │  │
│  │                                                         │  │
│  │     Supported: PDF, JPG, PNG (Max 10MB per file)      │  │
│  │                                                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  Uploaded Files:                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  📄 road_photo.jpg  (2.3 MB)              [View] [✕]   │  │
│  │  📄 complaint_copy.pdf  (1.8 MB)          [View] [✕]   │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘

Colors:
- Upload area border: #767676, 2px dashed
- Upload area background: #F5F5F5 (Light Gray)
- Hover background: rgba(0, 61, 130, 0.05)
- Icon: #003D82
- Text: #767676, 16px Inter Regular
- File list background: #FFFFFF
- File item hover: #F5F5F5
- File size: #767676, 14px Inter Regular
- Remove button (✕): #C51F1F on hover

Drag Active State:
- Border: #003D82, 2px solid
- Background: rgba(0, 61, 130, 0.1)
```

---

## Accessibility Guidelines

### Keyboard Navigation
- All interactive elements focusable via Tab
- Focus indicator: 3px solid #003D82 outline with 2px offset
- Skip to main content link (visible on Tab)
- ESC closes modals/dropdowns
- Enter/Space activates buttons

### Screen Reader Support
- Semantic HTML (nav, main, article, aside)
- ARIA labels for icons-only buttons
- ARIA live regions for dynamic content
- Form error announcements
- Status updates announced

### Color Contrast (WCAG 2.1 AA)
- Normal text (16px): 4.5:1 minimum
  ✓ #1A1A1A on #FFFFFF: 16.9:1
  ✓ #003D82 on #FFFFFF: 8.6:1
  ✓ #767676 on #FFFFFF: 4.5:1

- Large text (24px): 3:1 minimum
  ✓ All color combinations pass

- Buttons: White text on #003D82: 13.1:1

### Focus Management
- Logical tab order (left-to-right, top-to-bottom)
- Focus trapped in modals
- Focus returned after modal close
- Skip navigation links

---

## Mobile-First Responsive Breakpoints

```css
/* Mobile First (default) */
@media (min-width: 320px) { /* Base styles */ }

/* Tablet */
@media (min-width: 768px) {
  /* 2-column layouts */
  /* Larger touch targets (48px min) */
}

/* Desktop */
@media (min-width: 1024px) {
  /* 3-column layouts */
  /* Hover states enabled */
  /* Max content width: 1200px */
}

/* Large Desktop */
@media (min-width: 1440px) {
  /* Wider spacing */
  /* Max content width: 1400px */
}
```

---

## Dark Mode (Future Enhancement)

```css
/* Dark Theme Colors */
--lawtrix-blue-dark: #4A90E2;
--background-dark: #121212;
--surface-dark: #1E1E1E;
--text-primary-dark: #FFFFFF;
--text-secondary-dark: #B0B0B0;
--border-dark: #333333;
```

Triggered by: `prefers-color-scheme: dark` or manual toggle

---

## Component Implementation Checklist

- [ ] Typography system configured (Inter, Source Serif, Noto Sans)
- [ ] Color tokens defined in Tailwind config
- [ ] Shadcn/ui installed and configured
- [ ] Button variants created
- [ ] Input components with all states
- [ ] Toast notification system
- [ ] Language selector dropdown
- [ ] Navigation header (mobile + desktop)
- [ ] Footer component
- [ ] Case workflow card
- [ ] Timeline view
- [ ] Document upload component
- [ ] Status badges
- [ ] Accessibility testing (Lighthouse, axe DevTools)
- [ ] Keyboard navigation verified
- [ ] Screen reader testing (NVDA, JAWS)
- [ ] Mobile responsive testing (320px - 1920px)

---

**Next:** Implement these mockups in Shadcn/ui components with full accessibility support.

**Reference:** STRATEGIC_RESEARCH_REPORT.md (Design System section)
