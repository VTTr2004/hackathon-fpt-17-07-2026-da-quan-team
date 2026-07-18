---
name: Premium Roast Appraisal
colors:
  surface: '#fdf9f4'
  surface-dim: '#ddd9d5'
  surface-bright: '#fdf9f4'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f7f3ee'
  surface-container: '#f1ede8'
  surface-container-high: '#ebe8e3'
  surface-container-highest: '#e6e2dd'
  on-surface: '#1c1c19'
  on-surface-variant: '#59413f'
  inverse-surface: '#31302d'
  inverse-on-surface: '#f4f0eb'
  outline: '#8d706e'
  outline-variant: '#e1bebc'
  surface-tint: '#b2282e'
  primary: '#900a1a'
  on-primary: '#ffffff'
  primary-container: '#b2282e'
  on-primary-container: '#ffccc9'
  inverse-primary: '#ffb3af'
  secondary: '#7b5647'
  on-secondary: '#ffffff'
  secondary-container: '#feccba'
  on-secondary-container: '#7a5446'
  tertiary: '#653d00'
  on-tertiary: '#ffffff'
  tertiary-container: '#815416'
  on-tertiary-container: '#ffcf9a'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdad7'
  primary-fixed-dim: '#ffb3af'
  on-primary-fixed: '#410005'
  on-primary-fixed-variant: '#900a1a'
  secondary-fixed: '#ffdbce'
  secondary-fixed-dim: '#ecbcaa'
  on-secondary-fixed: '#2e140a'
  on-secondary-fixed-variant: '#613e31'
  tertiary-fixed: '#ffddb9'
  tertiary-fixed-dim: '#f8bb73'
  on-tertiary-fixed: '#2b1700'
  on-tertiary-fixed-variant: '#663e00'
  background: '#fdf9f4'
  on-background: '#1c1c19'
  surface-variant: '#e6e2dd'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-bold:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style

This design system blends the precision of financial analysis with the warmth of a premium café experience. The personality is **sophisticated, grounded, and inviting**. It avoids the clinical coldness typically associated with SaaS tools, instead opting for a "Clubhouse" aesthetic—where high-stakes deals are discussed over artisanal coffee.

The visual style is **Corporate / Modern with a Tactile twist**. We leverage heavy whitespace and systematic typography but ground them in a palette of organic tones. The UI should evoke a sense of heritage and reliability, using subtle depth and rich textures to make complex data feel accessible and human-centric.

## Colors

The palette is derived from the "Highlands Coffee" visual identity, adapted for a high-fidelity interface:

- **Primary (#B2282E):** A deep, authoritative brand red used for primary actions, critical alerts, and brand accents. It provides high energy and clear hierarchy.
- **Secondary (#4B2C20):** A rich Espresso brown used for headers, text, and structural elements to provide a softer, more premium alternative to pure black.
- **Tertiary (#D9A05B):** A warm Oak/Gold tone used for highlights, progress indicators, and secondary visual interest.
- **Neutral (#F9F5F0):** A Cream/Parchment base that serves as the primary surface color, reducing eye strain compared to pure white and reinforcing the "premium café" atmosphere.

## Typography

We utilize **Inter** for its exceptional legibility in data-dense financial environments. To align with the warmer brand narrative:

- **Headlines:** Use tighter letter spacing and Semi-Bold weights in Espresso (#4B2C20) to create a strong, professional anchor.
- **Body Text:** Maintained at 16px for optimal readability against the cream background. High-contrast dark brown text ensures accessibility.
- **Labels:** Use uppercase tracking for a "menu-style" editorial feel in navigation and small headers.
- **Numerical Data:** Tabular figures should be enabled to ensure financial tables align perfectly.

## Layout & Spacing

The layout follows a **Fluid Grid** model with generous margins to mimic the airy feel of a flagship cafe.

- **Grid:** 12-column system for desktop, 4-column for mobile.
- **Rhythm:** An 8px linear scale governs all padding and margins.
- **Density:** We employ a "Comfortable" density setting. Data tables should have ample row padding (16px vertical) to prevent the UI from feeling cramped or overly technical.
- **Adaptation:** On mobile, side margins shrink to 16px, and complex multi-column dashboard widgets stack vertically to maintain legibility.

## Elevation & Depth

Hierarchy is established through **Tonal Layers** rather than heavy shadows. 

- **Surfaces:** The base layer is the neutral Cream (#F9F5F0). Elevated cards use a pure white surface with a very subtle 1px stroke in a light wood tone (#E5DED5).
- **Shadows:** Use "Ambient Coffee" shadows—low-opacity (8-12%) blurs with a slight brown tint (#2A1A14) to create a soft, organic lift.
- **Interactive States:** Hovering over a card should slightly deepen the shadow and shift the border color to the Tertiary Gold tone.

## Shapes

The shape language is **Rounded**, reflecting the organic nature of coffee beans and high-end furniture.

- **Primary Radius:** 0.5rem (8px) for buttons, inputs, and small components.
- **Container Radius:** 1rem (16px) for cards and modals to create a friendly, approachable frame for complex data.
- **Interactive Elements:** Buttons utilize the 0.5rem radius, providing a modern yet soft feel that avoids the aggressiveness of sharp corners.

## Components

- **Buttons:** Primary buttons are Solid Brand Red (#B2282E) with white text. Secondary buttons use an Espresso border with Espresso text.
- **Input Fields:** Use a subtle cream fill (#F3EEE8) with a bottom-only or soft-border focus state in Gold (#D9A05B).
- **Chips/Badges:** Use "Roast Levels" for status—Light (Cream/Gold), Medium (Tan/Brown), and Dark (Espresso/White).
- **Cards:** Cards are the primary vessel for appraisal data. They should feature a 16px internal padding and a subtle 1px border.
- **Data Tables:** Headers should be Espresso (#4B2C20) with light cream dividers. Alternate row striping is discouraged; use subtle hover states instead to keep the look clean and premium.
- **Charts:** Use a custom theme of Red, Gold, and Espresso for data visualization to maintain brand harmony.