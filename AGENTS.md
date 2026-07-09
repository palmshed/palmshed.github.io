# Design principles

1. **Inform before persuade.** The page explains the organization. Any positive impression should come from the work itself.
2. **One purpose per section.** Every section must have a distinct job. If two sections overlap, merge them. If a section cannot justify its existence, remove it.
3. **Typography establishes hierarchy.** Use typography, spacing, and document structure before introducing decorative elements.
4. **Fewer concepts are better.** Prefer removing over adding. If something can be removed instead of improved, remove it.
5. **Capabilities over technologies.** Describe what you build, not which frameworks or tools you use. The page will age better.
6. **Static by design.** Prefer static documents over application logic. Introduce frameworks or client-side behavior only when they solve a demonstrated problem.
7. **Software over website.** The page documents the engineering organization. It is not a marketing site or a product landing page.
8. **Justify every addition.** Every new section, component, interaction, or abstraction should justify why the existing structure cannot express the same information. Prefer removing, merging, or simplifying before adding.
9. **Inevitable structure.** Nothing should look like it was added because it could be. Everything should appear because it is necessary to understand the organization.
10. **Patterns are earned.** Do not abstract a pattern before it has appeared at least three times. Until then, duplication is often simpler than abstraction. A new reusable component should emerge from repeated natural solutions, not from anticipating future needs.
11. **Stability over novelty.** Once a pattern has proven itself, changing it requires stronger justification than introducing it originally. Familiarity is part of the design.
12. **Repositories should reflect the page.** Keep the codebase as quiet as the site. Documentation, structure, and tooling should be understandable without reading implementation details.

# Writing guidelines

- Prefer short, direct sentences.
- Avoid em dashes, exclamation marks (except for critical notices), and words like "amazing", "exciting", "incredible", "powerful".
- Let the content speak for itself. If something feels like it is trying to attract attention, simplify or remove it.
- Announcement bar: if there is nothing important to announce, remove it. If it stays, one short sentence, no exclamation marks, no marketing phrasing.
- This is an open source engineering organization site. Write with the understated tone of LLVM, Rust, or OpenBSD. State what something is without trying to persuade.

# Interaction guidelines

Interactions should reveal capability, not compensate for layout.

Before adding a hover or popover interaction, ask whether the information needs to be hidden in the first place. If the page works as a static, predictable document, prefer always-visible text or a native `<details>` disclosure. Only introduce a hover pattern if the same interaction is likely to be reused across multiple locations on the page.

If adding context to static elements (e.g. metrics), prefer:

- Tooltip on hover (quiet, no layout shift)
- Native `<details>` disclosure matching the Repository Archive pattern
- Small always-visible secondary line of text

Avoid on this page:

- Sliding panels, drawers, popover modals
- Horizontal carousels
- Animated cards or shift-on-hover content
- Interaction patterns that don't exist anywhere else on the page

If the page has succeeded by being static and predictable, introducing a single interactive element makes that one part behave differently from the rest of the site. That should be the exception, not the default.

Before changing visual weight, identify what currently carries the reader's attention. Change only elements that compete with it.
