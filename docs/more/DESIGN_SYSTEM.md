**Note:** This design system was created prior to implementing the app. Some components and features described here may not exist in the current codebase.

---

Below is a **complete Design System Document for *VibeCraft*** — structured like a professional product team spec (similar to Figma/Notion design systems).
It gives you: identity, color tokens, spacing, grids, typography, components, interaction patterns, motion rules, and voice/tone.

You can drop this into your repo as `DESIGN_SYSTEM.md`.

---

# 🎨 **VibeCraft Design System**

## **Version**

1.0 · Synesthetic Visual Identity · November 2025

## **Purpose**

The **VibeCraft Design System** ensures a cohesive, expressive, music-driven experience across web, product UI, and marketing assets. It reflects VibeCraft’s core mission:

> **Transform music into motion using AI-driven synesthetic visuals.**

The design system balances **artistic expression** with a **clean, cinematic UI** musicians feel comfortable working in.

---

# 1. **Brand Identity**

## 1.1 Brand Pillars

* **Synesthesia** — sound becomes color, rhythm becomes motion.
* **Creative Empowerment** — musicians feel powerful & inspired.
* **Minimal Tech, Maximum Aesthetic** — UI disappears behind the experience.
* **Night-Studio Energy** — neon accents on dark surfaces.
* **Effortless Flow** — intuitive, modern, fluid.

## 1.2 Personality

* Artistic
* Innovative
* Supportive
* Cinematic
* Calm but expressive

## 1.3 Voice & Tone

* Encourage creativity, never overwhelm.
* Speak like a trusted creative companion, not a machine.
* Short lines. Minimal jargon.
* Examples:

  * “Drop your track. We’ll handle the visuals.”
  * “This chorus has serious energy.”
  * “Let’s bring this verse to life.”

---

# 2. **Color System**

VibeCraft has a **dark-first**, neon-accent palette inspired by synthwave, audio meters, and cinematic UIs.

## 2.1 Core Palette

| Token                   | Value     | Usage                                 |
| ----------------------- | --------- | ------------------------------------- |
| `--vc-bg`               | `#0C0C12` | Primary app background                |
| `--vc-surface`          | `#15151F` | Cards, panels, modals                 |
| `--vc-accent-primary`   | `#6E6BFF` | Primary CTA, highlights               |
| `--vc-accent-secondary` | `#FF7EFA` | Secondary accent for selection, pulse |
| `--vc-accent-tertiary`  | `#00E1D9` | Success, generative states            |
| `--vc-text-primary`     | `#FFFFFF` | Core text                             |
| `--vc-text-secondary`   | `#B6B6C9` | Subtle text, labels                   |
| `--vc-error`            | `#FF5A75` | Errors                                |
| `--vc-warning`          | `#FFBD59` | Warnings                              |
| `--vc-border`           | `#2A2A36` | Dividers, panel edges                 |

## 2.2 Extended Gradients

| Name                  | Gradient                                         |
| --------------------- | ------------------------------------------------ |
| **Primary Glow**      | linear-gradient(90deg, #6E6BFF 0%, #8F7BFF 100%) |
| **Synesthetic Pulse** | linear-gradient(135deg, #FF7EFA, #00E1D9)        |
| **Ambient Drift**     | radial-gradient(circle, #1B1B27, #0C0C12 80%)    |

## 2.3 Elevation Tokens

| Token      | Shadow                      |
| ---------- | --------------------------- |
| `--elev-1` | 0 1px 4px rgba(0,0,0,0.25)  |
| `--elev-2` | 0 4px 12px rgba(0,0,0,0.35) |
| `--elev-3` | 0 8px 24px rgba(0,0,0,0.45) |

---

# 3. **Typography System**

## 3.1 Typefaces

* **Primary UI Font:** *Inter* or *Söhne*
  Clean, modern, legible at all sizes.

* **Display Font (for headings):** *Space Grotesk* or *Monument Extended*
  Offers a bold cinematic punch.

## 3.2 Type Scale

| Role   | Font       | Size    | Weight  | Letter-spacing |
| ------ | ---------- | ------- | ------- | -------------- |
| H1     | Display    | 48–64px | 600–700 | -1%            |
| H2     | Display    | 36–40px | 600     | -0.5%          |
| H3     | Display/UI | 28–32px | 600     | 0              |
| H4     | UI         | 20–24px | 500     | 0              |
| Body L | UI         | 18px    | 400     | 0              |
| Body M | UI         | 16px    | 400     | 0              |
| Body S | UI         | 14px    | 400     | 1%             |
| Label  | UI         | 12px    | 500     | 3%             |

---

# 4. **Spacing & Layout**

## 4.1 Spacing Scale

| Token        | px   |
| ------------ | ---- |
| `--space-2`  | 2px  |
| `--space-4`  | 4px  |
| `--space-8`  | 8px  |
| `--space-12` | 12px |
| `--space-16` | 16px |
| `--space-20` | 20px |
| `--space-24` | 24px |
| `--space-32` | 32px |
| `--space-48` | 48px |
| `--space-64` | 64px |

## 4.2 Layout System

* **Max content width:** 1200px
* **Grid:** 12-column responsive grid
* **Card radius:** 12–16px
* **Interactive radius:** 8px

---

# 5. **Iconography & Illustration**

## 5.1 Icon Style

* Mono-stroke
* Rounded corners
* Slight neon glow optional on hover
* Use 24px base size, 2px stroke

## 5.2 Illustrative Motifs

Icons and illustrations draw from **sound and motion**:

* Waveforms
* Blurred streaks
* Repeating geometry
* Prism splits
* Motion lines
* VU meter bars

---

# 6. **Motion & Animation System**

Motion is critical for VibeCraft — it reinforces the idea of **music → motion**.

## 6.1 Motion Principles

* Smooth, continuous, never jerky
* Easing: `cubic-bezier(0.4, 0.0, 0.2, 1)` (Material-like)
* Use pulses, waves, and glows as animated feedback

## 6.2 Core Animations

| Name                | Purpose                              | Timing     |
| ------------------- | ------------------------------------ | ---------- |
| **Pulse**           | Playback, generation, waiting states | 1.8s loop  |
| **Wave Sweep**      | Section highlight animation          | 1.2s       |
| **Beat Flash**      | Visual emphasis on beat detection    | 140ms      |
| **Glow Fade**       | Button hover                         | 250ms      |
| **Ambient Fractal** | Background animation (subtle)        | continuous |

---

# 7. **Components**

Below are the components musicians interact with most.

---

## 7.1 **Button**

**Variants:**

* Primary (neon violet)
* Secondary (cyan outline)
* Ghost (low-emphasis)

**Primary Example:**

* Background: `--vc-accent-primary`
* Hover: brighter + slight glow
* Active: compress 1–2px

---

## 7.2 **Card**

Used for section cards, video previews, etc.

* Background: `--vc-surface`
* Border: `--vc-border`
* Radius: `16px`
* Elevation: `--elev-1`
* Hover: increase elevation, add subtle neon edge

---

## 7.3 **Section Card**

Contains:

* Section type (“Chorus 1”)
* Duration
* Lyric snippet
* Mood tags
* Generate/Regenerate buttons

**Color Tagging Rule:**
Use a subtle color bar to reflect mood:

| Mood             | Color               |
| ---------------- | ------------------- |
| Chill / Lofi     | #7FCBFF (baby blue) |
| Energetic        | #FF7EFA (magenta)   |
| Dark / Emotional | #6E6BFF deep violet |
| Upbeat / Happy   | #00E1D9 aqua        |

---

## 7.4 **Video Preview Frame**

* Rounded corners 12–16px
* Dark frame
* Glow ring during generating
* Timecode overlay in top-left
* “Use in Full Video” pill in bottom-right

---

## 7.5 **Progress Indicators**

Three styles:

### Pulse Bars

```
▮ ▮ ▮
```

Synced in staggered animation.

### Waveform Sweep

A shimmering bar that travels left → right.

### Section Timeline Loader

Fills section-by-section as analysis completes.

---

# 8. **Templates (Video Style Presets)**

These become your presets for music creators.

## **1. Abstract Visualizer**

* Floating shapes
* Light streaks
* Deep violets & neons
* Best for EDM/ambient/lofi

## **2. Mood Environment**

* Cozy room
* Foggy forest
* Neon city
* Best for indie, pop, R&B

## **3. Character Focus (future)**

* Animated figure in consistent style
* More advanced

---

# 9. **Accessibility**

* Minimum text contrast: 4.5:1
* Hover states for all controls
* Text alternatives for all icons
* Avoid neon-only elements without outline

---

# 10. **Brand Assets Summary**

**Logo:** waveform prism
**Accent style:** neon glow
**Primary color:** electric violet
**Vibes:** synesthetic, cinematic, expressive, intuitive

---

# Want the next layer?

I can create:

### ✔ Full Tailwind config for this design system

### ✔ SVG logo concepts for VibeCraft

### ✔ Component library in React (code-level)

### ✔ UI mockups (dark mode)

### ✔ Style sheet for marketing/onboarding pages

Just tell me which one you want next.
