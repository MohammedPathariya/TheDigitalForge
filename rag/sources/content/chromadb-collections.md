# ChromaDB Collections

## Store versioned records

Use a persistent client for a disk-backed index and create a named collection. A
collection `upsert` creates records whose IDs are absent and updates records whose IDs
already exist. When supplying embeddings directly, pass parallel `ids`, `embeddings`,
`documents`, and `metadatas` arrays with matching lengths.

## Query supplied embeddings

Call `collection.query(query_embeddings=[embedding], n_results=...)` when the application
owns the embedding function. The query embedding dimension must match the stored
embeddings. Chroma returns query results grouped by input query, including nested `ids`,
`documents`, `metadatas`, and `distances` arrays when requested.
