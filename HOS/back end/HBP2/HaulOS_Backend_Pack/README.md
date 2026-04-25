# HaulOS Backend Pack

This pack consolidates the backend we designed today into one coherent starter backend for HaulOS.

## Included
- FastAPI API
- PostgreSQL / PostGIS-ready SQLAlchemy models
- Alembic migration scaffold
- Heavy vehicle routing engine starter
- Managed passage logic
- Mount Magnet **contra flow** rule
- RTAA / trailer reconfiguration logic
- Combination type + platform type support
- Bridge / powerline / fuel / rest area models
- Bridge CSV / GeoJSON preview + import
- Saved import profiles
- Spatial conflict endpoints

## Key product rules built in
- Combination type and platform type are separate
- Semi, B-double, road train, short triple, etc. are network classes
- Flat top, drop deck, low loader, tanker, skel, etc. are platform types
- Rest area is not the same as RTAA
- Inland north triple road train planning can stage via **Wubin RTAA**
- Coastal north triple road train planning can stage via **Carnarvon RTAA**
- Mount Magnet managed passage can raise a **Contra flow required** event
- Hazard, fuel, and rest intelligence are shown to the driver instead of hidden
- Managed passage routes are returned when physically workable, but blocked from departure until required actions are completed

## Suggested run order
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
createdb haulos
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/haulos"
uvicorn app.main:app --reload
```

Open:
- `http://127.0.0.1:8000/docs`

## Notes
This is a serious backend starter, not a complete production transport platform yet.
You still need:
- real Main Roads WA network data
- real bridge / powerline source datasets
- authentication
- user / fleet roles
- live GPS ingestion
- background jobs / notifications
- map frontend
