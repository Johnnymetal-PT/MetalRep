PG Mielectro Crawler Bot Compatibility Layer

This package now delegates to the generic crawler platform in:
- [README.md](/c:/Users/Utilizador/Desktop/Repos/Hipermercado/pg_crawler_bot/README.md)
- [pg_app.py](/c:/Users/Utilizador/Desktop/Repos/Hipermercado/pg_crawler_bot/pg_app.py)

You can still run the old command:

```powershell
uvicorn pg_mielectro_crawler_bot.pg_app:app --host 0.0.0.0 --port 8000
```

But the preferred new command is:

```powershell
uvicorn pg_crawler_bot.pg_app:app --host 0.0.0.0 --port 8000
```

The specific `mielectro.es` extraction logic now lives in:
- [pg_mielectro.py](/c:/Users/Utilizador/Desktop/Repos/Hipermercado/pg_crawler_bot/pg_adapters/pg_mielectro.py)
