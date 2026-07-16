# OpenAI Responses API

## Create a response

Use `client.responses.create(model=..., instructions=..., input=...)` with the OpenAI
Python SDK. The `model` selects the model, `instructions` supplies developer-level
guidance for that request, and `input` supplies text, image, or file input items. Set
`store=False` when the generated response must not be stored for later API retrieval.

## Read text and usage

For a completed response, `response.output_text` is the SDK convenience property for the
aggregated text output. Token accounting is available from `response.usage`, including
`input_tokens` and `output_tokens` when usage information is present.

## Source scope

These notes are pinned to OpenAI Python SDK 2.45.0 and OpenAI OpenAPI document version
2.3.0 for `POST /v1/responses`. They intentionally exclude Chat Completions examples so
retrieval does not encourage the wrong API surface.
