RELOAD="--reload"
if [[ $1 == "--no-reload" ]]; then
  RELOAD=""
fi

uv run --env-file=.env uvicorn api.app:app --host 0.0.0.0 --port 8765 --no-access-log ${RELOAD}
