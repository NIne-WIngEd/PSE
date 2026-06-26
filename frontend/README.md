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


## License

This frontend is licensed under the GNU Affero General Public License,
version 3 or later (`AGPL-3.0-or-later`). See the repository-level
`LICENSE` and `NOTICE` files.

A modified version made available to users over a network must provide the
corresponding source code as required by AGPL section 13. Keep a visible
link to the source repository in deployed versions.
