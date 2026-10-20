# Live Weather Travel App

Personal dashboard for **Jersey** live weather and travel (airport, Ports of Jersey, DFDS Saint Malo ↔ St Helier), plus forecasts for Cape Town, Johannesburg, London and Santa Barbara, and a Springboks fixture list in UK time with UK TV.

Trip planning and destination search are out of scope for v1. See [docs/requirements.md](docs/requirements.md).

## Documentation

- [Requirements](docs/requirements.md)
- [Data sources](docs/data-sources.md)
- [Architecture](docs/architecture.md)
- [UI](docs/ui.md)
- [Deployment](docs/deployment.md)

## Run locally

```bash
git clone https://github.com/Danzag88/Live_Weather_Travel_App.git
cd Live_Weather_Travel_App
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn server.main:app --reload --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Do not commit API keys or `.env` files. Use a local env file and keep secrets out of git.

## Email recipient admin (Snowflake)

A Streamlit in Snowflake app manages who receives the dashboard by email. It populates `SHARED_DB.PUBLIC.EMAIL_RECIPIENTS`. Run [snowflake/schema.sql](snowflake/schema.sql) if you need the table or starter rows, then use [snowflake/streamlit_app.py](snowflake/streamlit_app.py) as the Streamlit main file.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
