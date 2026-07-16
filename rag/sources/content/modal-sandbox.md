# Modal Sandbox

## Create an isolated sandbox

Create a sandbox with `modal.Sandbox.create(app=..., image=..., timeout=..., cpu=...,
memory=..., workdir=...)`. Set `block_network=True` to drop outbound network traffic.
The sandbox-level `timeout` limits the sandbox lifetime; CPU and memory parameters apply
resource limits to the sandbox.

## Execute and clean up

Run a command with `sandbox.exec(*args, timeout=..., workdir=..., env=...)`. The returned
container process exposes `stdin`, `stdout`, and `stderr`, and `wait()` returns its exit
status. Call `sandbox.terminate(wait=True)` to stop execution and `sandbox.detach()` to
release the client handle during cleanup.
