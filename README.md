# ER Triage Extractor — CCI Session 11

A small, **runnable** Django app: a triage nurse submits a patient's vitals and
chief complaint; the system assigns an ESI-like acuity (1–5) and flags suspected
oncologic emergencies; the on-call doctor sees a live queue sorted by acuity.

This is the app you **tour in Lesson 5**, **extend in Lesson 6** (add a `dashboard`
app), and **deploy to Render in Lesson 7**.

> ⚠️ Teaching app. Not for clinical use.

## Run it locally (5 minutes)

```bash
cd er_triage_app
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # then paste your OpenAI key into .env (optional)

python manage.py migrate
python manage.py seed_demo         # adds 5 demo patients so the queue isn't empty
python manage.py runserver
```

Open <http://127.0.0.1:8000/> — the doctor queue.
- **/triage/new** — the nurse form.
- **/** — the doctor queue.
- **/admin** — Django admin (run `python manage.py createsuperuser` first).

### About the OpenAI key
The oncologic-emergency extractor calls OpenAI. **Without a key the app still
runs** — triages are saved with `extractor_status="failed"` and no flags. With a
key in `.env` (`OPENAI_API_KEY=...`), the chief complaint is sent to the model and
flags come back. The key is read from the environment and is never committed.

## Run the tests

```bash
python manage.py test
```

13 tests: the acuity rules, the extractor's closed-set + graceful degradation, and
the form/queue end-to-end (the LLM is mocked — no network in tests).

## Project layout

```
er_triage_app/
├── manage.py
├── requirements.txt
├── render.yaml            # Render blueprint (Lesson 7)
├── build.sh               # Render build step
├── .env.example
├── er_triage/             # the PROJECT (settings, root urls, wsgi)
│   ├── settings.py        #   INSTALLED_APPS lives here
│   └── urls.py
└── triage/                # the APP (the actual triage feature)
    ├── models.py          # Patient, TriageEvent
    ├── forms.py           # NurseTriageForm
    ├── views.py           # nurse form, confirmation, queue, detail
    ├── urls.py
    ├── crypto.py          # MRN obfuscation + name encryption
    ├── services/
    │   ├── acuity.py                 # deterministic — never the LLM
    │   └── oncologic_emergency.py    # the LLM call, degrades gracefully
    ├── templates/triage/  # base, nurse_form, confirmation, queue, detail
    ├── management/commands/seed_demo.py
    └── tests/
```

## Deploy to Render (Lesson 7)

1. Push this folder to a GitHub repo.
2. On Render: **New + → Web Service → connect the repo**. Render reads `render.yaml`.
3. In the dashboard, paste `OPENAI_API_KEY` and `FERNET_KEY` (both marked `sync: false`).
4. Deploy. Render runs `build.sh` then `gunicorn er_triage.wsgi`.

The blueprint uses **SQLite on a 1 GB persistent disk** — the simplest option. To
use Postgres instead, remove the `disk:` block, add a Render Postgres database, and
set `DATABASE_URL`.
