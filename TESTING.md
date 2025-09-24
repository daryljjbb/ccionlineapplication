# Running tests and the dev server (CI-friendly)

This project uses the included virtualenv at `./env`.

Run the Django test suite for the `webapp` app:

```bash
./env/bin/python webapplicationtutorial/manage.py test webapp -v 2
```

Run the full test suite:

```bash
./env/bin/python webapplicationtutorial/manage.py test -v 2
```

Start the development server:

```bash
./env/bin/python webapplicationtutorial/manage.py runserver
```

If you're running in CI, use the test runner command above; Django will create a temporary test database and run migrations.

Notes:
- Tests are under `webapplicationtutorial/webapp/tests` or `webapplicationtutorial/webapp/tests.py` depending on your layout.
- If your CI environment doesn't include the `env` virtualenv, install dependencies from `requirements.txt` (create one if missing) and run `python -m venv .venv` then install.
