# Project Structure Setup

Based on the Technology Stack and Component structure extracted from `architecture.md` (Full shape) or detected from the project (Minimal shape):

1. **Create directory structure** following framework conventions.
2. **Initialize project files** (`package.json`, `pyproject.toml`, `Cargo.toml`, etc.).
3. **Install dependencies** from Technology Stack + External Dependencies.
4. **Configure build** (`tsconfig`, `vite.config`, `esbuild`, etc.).
5. **Create a minimal entry point** — a **running** application, not just a compile target:
   - Web app → dev server serves a page.
   - VS Code extension → extension activates + panel opens.
   - CLI → `--help` prints usage.
   - API → health check returns 200.
