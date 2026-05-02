# Backend Learning Notes

This folder will eventually contain the FastAPI backend.

Do not write FastAPI code first.

Recommended order:

1. Build reconciliation logic as plain Python functions.
2. Add tests.
3. Add a CLI.
4. Wrap stable functions with FastAPI routes.
5. Add database and queue.

## Future Modules

```text
app/core
  canonical models, domain profiles, configuration

app/services
  file loading, normalization, matching, validation, reporting

app/agents
  LangGraph orchestration nodes

app/api
  FastAPI routes
```
