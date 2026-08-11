# Run Instructions

## Folder structure

implementations_MODE/
-- checkpoint_X/
---- requirements.txt
---- package.json
-- data

## Run backend

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

## Run frontend

```
npm install
npm run dev
```

If it does not work (vite is broken) then do:

```
node node_modules/vite/bin/vite.js --host 0.0.0.0
```
