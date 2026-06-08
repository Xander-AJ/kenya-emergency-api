# Examples

Runnable examples and integration sketches for `kenya-emergency`. The three
scripts run cleanly today against the test fixtures (they set
`KENYA_EMERGENCY_SNAPSHOT_DIR` themselves); when v1.0 ships verified data,
they work against the bundled snapshots with no env vars at all.

| Example | What it shows |
| --- | --- |
| [`01_python_client.py`](./01_python_client.py) | Direct `EmergencyService` usage — county lookups, category-filtered contacts, national numbers, the `emergency_overview` composite, and `DataNotFoundError` / `ValueError` handling. |
| [`02_running_the_api.py`](./02_running_the_api.py) | Start the FastAPI server programmatically with `uvicorn.run`, with the equivalent shell command and a production CORS note. |
| [`03_curl_examples.sh`](./03_curl_examples.sh) | Eight `curl` calls against a running server — happy paths plus a 404 and a 400 error path, each printing its HTTP status. |
| [`04_integration_pattern.md`](./04_integration_pattern.md) | Design sketch of the `EmergencyContactProvider` Protocol seam and how `kenya-emergency` composes with [`rag-guardrails-starter`](https://github.com/Xander-AJ/rag-guardrails-starter). |

## Running them

```bash
# 1. Python client (standalone)
python examples/01_python_client.py

# 2. Start the API server (leave it running)
python examples/02_running_the_api.py

# 3. In another terminal, hit the running server
bash examples/03_curl_examples.sh
```
