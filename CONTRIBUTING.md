# Contributing

## Design principles

This site follows an understated, institutional tone. See AGENTS.md for full
guidelines. The short version: prefer short sentences, avoid decorative
punctuation and promotional language, and let the content speak for itself.

## Layout

- `.github/site/` ~ the static site. Each page is a standalone HTML file with
  its own `<style>` block. There is no framework or build step.
- `auth/` ~ the authentication backend (separate Vercel project). See
  `auth/README.md` and `AUTH.md`.

Pages are edited by hand. The site is served from GitHub Pages; pushing to
`main` deploys it (see `.github/workflows/deploy-site.yml`).

## Adding a project

Projects are listed on two pages:

- `projects.html` ~ the **Overview** carousel and the **All repositories** grid.
- `index.html` ~ the homepage **Capabilities** section (hover previews).

To add a project to the Overview carousel in `projects.html`, copy an existing
`<div class="slide">` block inside `#track` and set:

- `slide-name` ~ the project name
- `slide-tag` (optional) ~ a quiet qualifier such as `upstream`
- `slide-desc` ~ one short sentence
- `slide-mock` ~ a small terminal mock (`.mock` with `.mock-head`,
  `.mock-muted`, `.mock-accent`, etc.)

Keep mocks quiet: use the site palette, not bright syntax colors. One project
per slide; the dots below the carousel update automatically from the slide count.

To add the same project to the **All repositories** grid, add a `<a class="card">`
block following the existing pattern (name, description, optional tag).

## Homepage capabilities

The `index.html` Capabilities list shows a preview on hover. Each item pairs a
list entry with a `.cap-preview` block. Add both together so the hover works.

## Authentication backend

Changes to `auth/` are deployed separately to Vercel. See `auth/README.md` for
local dev and deploy steps. Do not commit secrets; set them as Vercel env vars.
