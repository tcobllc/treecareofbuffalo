# Tree Care of Buffalo — DESIGN.md

The persistent brand system. Agents: read this before touching markup, styles, imagery,
or copy. It outranks generic taste. Companion gates: `tools/predeploy.py`,
`.claude/agents/design-review.md`.

## 1. Identity in one line

A golden-hour film about people who work in trees: deep pine darkness, warm amber light,
woodcut type, foreman's voice. Evolution of the live v1 world; never a white-editorial or
moody-atmospheric reskin (both were built and rejected).

## 2. Tokens (the source of truth is assets/site.css `:root`; index.html mirrors inline)

- `--canvas: #101a12` deep pine (page ground, never pure black)
- `--panel: #182619` / `--panel-2: #1e2f20` raised surfaces
- `--line: #2b3d2c` / `--line-strong: #4a6046` hairlines
- `--accent: #e8963a` amber gold (CTAs, kickers, rings) / hover `#f3a94e` / muted `#7a5a28`
- `--text-primary: #f3e6c9` warm cream / `--text-secondary: #c4b598`
- Type: `--display: Bevan` (woodcut serif, headings only) · `--body: Cabin` (400-700 variable)
  · `--mono: Courier Prime` (kickers, chips, nav, legal). All self-hosted latin woff2 in
  assets/fonts; no Google Fonts links (they cost ~700ms FCP and CLS).
- Radius scale: 8-10px controls, 12-16px cards, 18-20px panels. Never pill-everything.
- Header brand logo: 64px desktop, 52px under 560px, 44px under 360px (the 320px header
  cannot hold 52 + phone + MENU + CTA without clipping).
- Motion easing: `--ease: cubic-bezier(.22,.7,.24,1)`; ambient drift uses `--ease-soft`.

## 3. Light and imagery law

- Warm low golden evening light, or bright warm overcast. REJECTED, do not re-test:
  dark/moody/desaturated "atmospheric" stills, mossy look-up oak, storm-sky oak family.
- Action imagery must survive a tree professional's glance: saw visibly biting wood or no
  tools in frame; rigging follows real protocol (ground crew unties, line runs back up);
  no flying debris chunks; no butt-log end-face resting shots; helmets always; climbing
  lines are braided synthetic (green/amber braid), never jute or manila.
- Generated (Higgsfield) imagery is the atmosphere layer; real crew photography, when it
  exists, is the proof layer. Both, not either.
- Workflow: stills first (cinematic_studio_2_5, 2k), inspect against these rules, animate
  only approved frames (kling3_0 pro). Grammar and recipes: tcob-higgsfield-cinema skill.

## 4. Copy law

- Foreman voice: short sentences, concrete nouns, plain promises.
- Banned words: solutions, seamless, passionate, premier, elevate, journey, cutting-edge,
  one-stop. Zero em dashes anywhere in shipped files.
- Locked facts: LLC est. 2024; claim only "10+ years in the trees" (industry experience);
  (716) 601-8275; business@treecareofbuffalo.com; Mon-Fri 7 AM to 7 PM, storm calls
  anytime; fully insured (GL + workers' comp); NO certifications (no ISA/TCIA), never imply.
- Never invent reviews, ratings, badges, awards, testimonials, or before/afters.
- Honesty beats punch: "Ground well below the surface, not just cut flush" replaced
  "roots and all" because grinding does not remove roots.

## 5. Motion specs (write motion this way: trigger, property, from-to, duration, easing)

- Reveals: on 18% viewport entry; opacity 0->1 + translateY 22->0; .7s; staggered .08s;
  hardened (observer + sweep fallback + self-stopping interval); no-JS override shows all.
- Pressed states (client favorite): every button `:active` translateY(1px) scale(.98) .08s.
- CTA halo: amber glow pulse on primary CTAs, 5-6s soft cycle. DELIBERATE.
- Kerf dividers: stroke-dashoffset draw-in on 60% entry, 1.6s.
- Hero scrub: 560vh desktop / 640vh mobile; six fractional caption bands; SKIP INTRO chip
  fast-forwards to the settle. Bands are fractions of hero progress, so length changes
  need no band edits.
- Ambient loops: `[data-ambient]` backgrounds get a muted looping video on min-width:861px
  only, gated on prefers-reduced-motion and Save-Data, falling back to the still + Ken Burns.
  Loops are seamless xfade tail-to-head encodes, <= 2 MB target.
- Everything respects prefers-reduced-motion: complete static page, final states pinned.

## 6. Reviewed tells (scanner exceptions, decided 2026-09-03)

`tools/devibe_scan.py` flags "neon glow" mediums here. Reviewed: the amber CTA halo and
the inset film vignettes on figures are DELIBERATE brand signatures (client-approved),
not AI defaults. The gate passes because highs = 0; do not "fix" these to appease the
scanner. Everything else it flags high gets fixed before deploy.

## 7. Conversion law (evidence-based, see SOURCESANDTOOLSINDEX.md §6)

- Calls convert far better than forms in this trade: call CTAs primary everywhere, form
  is the fallback. Sticky mobile bar: CALL NOW (amber) + FREE ESTIMATE, past 40% depth.
- Response promise next to CTAs and mean it (call-back within one business day).
- The estimate is the price; pay on completion; cleanup included. Say it near every ask.
- When real reviews exist: dated quotes beside the estimate form, never fabricated.
- The estimate form POSTs to the Cloudflare Pages Function (functions/api/lead.js:
  Turnstile Managed widget + Resend, secrets in both Pages environments, CORS for the
  GitHub Pages origin) and falls back to mailto on any failure. Leads deliver to the
  owner's Gmail until the domain is verified at Resend (October, with DNS control).
- Call-primary applied 2026-09-19: every CTA pair is phone (amber .btn) first, estimate
  (.btn.ghost) second: hero settle, static hero, homepage banner, service rows, all
  page closers, and the sticky rail on every generated page.

## 8. Structure

20 indexable pages: home, services hub + 5 service pages, /service-area/ hub + 8 town
pages, why-us, faq, estimate, privacy (+ reviews page noindex and out of the sitemap
until real reviews exist; booking.html and services/index.html redirect stubs; styled
404). Clean URLs (no .html), absolute canonicals on treecareofbuffalo.com. Schema:
HomeAndConstructionBusiness @id #business (name "Tree Care of Buffalo", legalName with
LLC, openingHoursSpecification, City objects) + FAQPage on home; Service + BreadcrumbList
on subpages, breadcrumb schema count must equal the visible crumbs (gated). Head-term
titles 30-70 chars, descriptions <= 160, sitemap lastmod per file (all gated by
tools/predeploy.py).

## 9. Subpage layout law (2026-09-19)

Every generated page (services/*, service-area/*, the hub) is a two-column `.page-grid`
at >1060px: `.page-main` (prose column, 60ch: Cabin's wide zero makes 68ch run ~100 characters) + `.rail` (sticky, top 112px). The rail is
one `.rail-card` (kicker TALK TO THE CREW, big phone link, hours line, four promise
bullets, ghost estimate link) and one `.rail-fig` (a banked golden still with a mono
caption). Rail figures rotate through the banked set so no two adjacent town pages share
one. Service page H1s carry the city ("Tree Removal in Buffalo"); prose runs 650-750
words on service pages and 450-520 on town pages, each town section built on a different
organizing device so the pages never read as copies. Below 1060px the rail stacks under
the prose. Progressive motion on site.css pages: scroll-driven reveals under
`@supports (animation-timeline: view())` (the JS reveal becomes a no-op there) and
cross-document `@view-transition` crossfades; both off under reduced motion.
