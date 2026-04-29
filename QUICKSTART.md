# Quickstart

1. `cd deploy`
2. `make init`
3. `make up-instance`
4. Open `http://localhost:23001` for the web app
5. Open `http://localhost:28001/docs` for the API docs
6. If the reverse proxy port is free, `http://localhost:10080/` will serve the same web app through Nginx

## Notes

- `make up-instance` starts the instance baseline stack from `compose.instance.yml` and includes kernel by default.
- `make start` is an alias of `make up-instance`.
- Baseline kernel is provided by the xiaocai repo under `adapters/kernel` and runs the real `flare-kernel` package.
- Stop the stack with `make stop`.
