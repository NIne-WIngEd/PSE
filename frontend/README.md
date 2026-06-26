# AFM frontend

Next.js interface for batch upload, mask review/editing, downstream analysis, and PDF export.

```bash
npm ci
npm run lint
npm run build
npm run dev
```

The backend URL defaults to `http://127.0.0.1:8050`. To change it, copy `.env.example` to `.env.local` and edit `NEXT_PUBLIC_BACKEND_URL`.

The frontend uses system fonts and does not download Google fonts during build, so production builds work in offline reviewer environments after dependencies have been installed.
