# Bookshelf landing page

The public Bookshelf landing page is a Vinext site. It presents the explicit
on-demand relevance flow, catalog provenance counts, bounded-input privacy
contract, and the evidence boundary for Codex, Claude, Pi, and Hermes adapters.

`pagecast/` is a self-contained static handoff bundle. Its fonts, licenses,
favicon, icon, final MP4, and poster are local.

Published Pagecast URL:
<https://pagecast-6cv.pages.dev/p/endlessly-brooding-cavern-29bf971e4f06b37e880793b556d0a682/>

## Local development

```bash
npm ci
npm run dev
```

## Validation

```bash
npm test
```

The test performs a production build and verifies the server-rendered HTML.
The social preview, poster, fonts, and MP4 for the app live under `public/`.
