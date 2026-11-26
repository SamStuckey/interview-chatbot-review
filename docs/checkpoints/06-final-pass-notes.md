# Final Pass Notes

Notes to incorporate into the README during the final review.

## Starting the app on a fresh install

1. Install and start Docker with Compose v2. No local Python installation is needed.
2. Clone the repository and open a terminal in its root directory.
3. Copy the configuration template:

   ```bash
   cp .env.example .env
   ```

4. Set `OPENAI_API_KEY` and `CAPPER_CACHE_KEY_SECRET` in `.env`. Generate a
   random cache-key secret with `openssl rand -hex 32`.
5. Build and start the app:

   ```bash
   docker compose up --build
   ```

   This keeps logs visible in the terminal. The `init` service creates signing
   keys, copies the supplied database, applies migrations, seeds demo data,
   and publishes content before the app starts. No separate migration command
   is needed on a fresh install.
6. Open <http://localhost:8000> and choose a demo user. The trace viewer is at
   <http://localhost:16686>. Both ports must be available.

Stop with Ctrl+C, or `docker compose down` from another terminal. Data stays
in the Docker volume. For later starts, use `docker compose up`; add `--build`
after changing code, dependencies, content, or the Dockerfile. Add `-d` only
when background operation is wanted.
