# FAVE Frontend

The FAVE frontend is a Vite, React, and TypeScript application for photo capture/upload, detection-mode selection, asynchronous diagnosis status, and localized recommendation display.

## Local Development

```bash
npm install
npm run dev
```

The development server defaults to `http://localhost:5173`. Set `VITE_API_URL` in `frontend/.env` to the reachable lightweight API proxy. The default local value is `http://127.0.0.1:8000`.

## Build and Lint

```bash
npm run build
npm run lint
```

## Vercel Deployment

Set the Vercel project root directory to `frontend`, use `npm run build` as the build command and `dist` as the output directory. Configure:

```text
VITE_API_URL=https://<your-render-service>.onrender.com
```

The frontend sends API calls to the Render proxy. Render forwards diagnosis and translation requests to the Modal inference API; the browser should not call Modal directly. Configure the production frontend origin in the Render `CORS_ORIGINS` and Modal `FRONTEND_ORIGIN` settings.

For architecture, Modal setup, environment variables, and known model/language limitations, see the [root project README](../README.md).
