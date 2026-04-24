# Lab 17 Multi-Memory Agent

Multi-memory agent built for the LangGraph lab with:

- short-term memory
- long-term preference memory
- episodic memory
- semantic memory
- benchmark comparing baseline vs memory-enabled agent
- Streamlit demo for chat and memory inspection

Detailed setup and run instructions are available in [INSTALL_AND_RUN.md](INSTALL_AND_RUN.md).

## Setup

```powershell
uv venv
.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
Copy-Item .env.example .env
```

Optional services:

- Redis for persistent preference memory
- Chroma for vector-style semantic retrieval
- OpenAI API for model-backed responses

The project still runs without those services by using local fallbacks.

For a fuller step-by-step guide, see [INSTALL_AND_RUN.md](INSTALL_AND_RUN.md).

## Run CLI demo

```powershell
python -m src.main --user-id user_001 --session-id session_1 --query "Tôi thích Python, không thích Java."
python -m src.main --user-id user_001 --session-id session_2 --query "Tôi nên học framework backend nào?"
```

Interactive mode:

```powershell
python -m src.main --user-id user_001 --session-id session_1
```

## Run Streamlit demo

```powershell
streamlit run src/demo/app.py
```

## Run benchmark

```powershell
python -m src.benchmark.run_benchmark
```

Outputs:

- [reports/benchmark_report.md](reports/benchmark_report.md)
- [reports/results.json](reports/results.json)

## Run tests

```powershell
pytest
```

## Notes

- The baseline agent only uses the current session context.
- The memory agent uses router-guided retrieval across four memory stores.
- If OpenAI is unavailable, the app falls back to a deterministic response synthesizer so the pipeline remains testable.
