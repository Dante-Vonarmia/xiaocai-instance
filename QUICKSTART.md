# Quickstart

1. `cd deploy`
2. `make init`
3. `make start`
4. Open `http://localhost:3001` for the web app
5. Open `http://localhost:8001/docs` for the API docs
6. If the reverse proxy port is free, `http://localhost/` will serve the same web app through Nginx

## Notes

- `make start` starts the instance-only baseline stack (`compose.instance.yml`).
- `devlib-flare-kernel` is development-only and is started only when `ENABLE_DEVLIB_FLARE=true` (or when using `make up-dev`).
- The mock kernel returns deterministic responses for acceptance checks; it does not implement the full FLARE engine.
- Stop the stack with `make stop`.
