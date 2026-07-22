# Security Policy

## Secret Handling

Do not commit real API keys, JWT secrets, database URLs, or production tokens.

Use environment variables for:

- `DEEPSEEK_API_KEY`
- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `CHROMA_PATH`
- `LOG_PATH`

## Rotation Checklist

Rotate secrets when:

- A key is pasted into a terminal, screenshot, issue, README, or chat.
- A collaborator leaves the project.
- A deployment platform account changes plan or ownership.
- A suspicious request or unexpected bill appears.

Recommended production actions:

- Rotate the DeepSeek API key in the provider console.
- Replace Railway `DEEPSEEK_API_KEY` with the new value.
- Replace Railway `JWT_SECRET_KEY` with a strong random value.
- Redeploy Railway after changing variables.

## Public Demo Safety

- Use fake embeddings on the hosted demo if model downloads are unstable or expensive.
- Avoid exposing admin logs with sensitive request bodies.
- Keep premium question banks and evaluation data private until the product direction is clear.
