# FastAPI Request and Response Models

## Request bodies

Define a request body as a Pydantic `BaseModel`, then annotate a path operation parameter
with that model. FastAPI reads the request body as JSON, validates it against the model,
and exposes the validated model instance to the path operation.

## Response models

Pass `response_model=ModelType` to `app.get`, `app.post`, or another path operation
decorator. `response_model` is a decorator argument, not a path operation function
argument. FastAPI uses it for response documentation, validation, conversion, and output
filtering. When both a return annotation and `response_model` are present, the explicit
`response_model` takes priority.

## HTTP errors

Raise `fastapi.HTTPException(status_code=..., detail=...)` to terminate request handling
and return an HTTP error response. Do not return an `HTTPException` object as ordinary
data.
