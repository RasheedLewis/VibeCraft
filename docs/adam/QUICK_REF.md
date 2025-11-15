# Quick Reference

## Do This

`make dev`

`make stop`

```bash
# you can run them individually but may get the venv prefix `((.venv) )` unless you VIRTUAL_ENV_DISABLE_PROMPT=1
# Lint
make lint-all # frontend and backend including format and -fix
make build # frontend only, Python doesn't build
make test
# Terminal 1: Frontend
cd frontend && npm run dev -- --host
# Terminal 2: Backend API
cd backend && source ../.venv/bin/activate && uvicorn app.main:app --reload
# Terminal 3: RQ Worker
cd backend && source ../.venv/bin/activate && rq worker ai_music_video
```

## More Notes

x
