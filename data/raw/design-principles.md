# Design Principles

Product design philosophy and UX guidelines at Acme Corp.

## Core Principles

### 1. Clarity Over Cleverness

Every interface should be understandable at a glance. Avoid jargon, ambiguous icons, and hidden interactions. If a user has to guess what something does, it's a design failure.

### 2. Progressive Disclosure

Show the most common actions by default. Nest advanced options behind expandable sections or secondary menus. Don't overwhelm beginners; don't slow down power users.

### 3. Consistency

Use established patterns over novel ones. Our design system (Acme UI) documents every component, its states (default, hover, active, disabled, error), and its usage rules. If a pattern doesn't exist, create it and add it to the system — don't improvise.

### 4. Feedback

Every user action must produce visible feedback within 100ms:

| Action | Feedback |
|---|---|
| Button click | Visual state change + result within 1 second |
| Form submit | Spinner/optimistic UI immediately |
| Error | Inline error message at the relevant field |
| Background task | Toast notification with progress |

### 5. Accessibility

All interfaces must meet WCAG 2.1 AA standards minimum:

- Color is never the sole indicator of state.
- All interactive elements are keyboard-navigable.
- Touch targets are at least 44×44px.
- Screen reader support with proper ARIA labels.

## Design Review Process

1. **Early review** — Share wireframes or low-fidelity mockups with the product team. Validate the flow before investing in high-fidelity.
2. **Design review** — Present high-fidelity designs in Figma. Stakeholders and at least one engineer review for feasibility.
3. **Implementation review** — Once built, compare the implementation against the design spec. Pixel-perfect is the goal, but accessibility and performance take priority.
