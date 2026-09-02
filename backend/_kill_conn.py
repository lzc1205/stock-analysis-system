from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Kill stale connections (not the current one)
    for conn_id in [117, 122, 124, 125]:
        try:
            db.execute(text(f"KILL {conn_id}"))
            print(f"Killed connection {conn_id}")
        except Exception as e:
            print(f"Failed to kill {conn_id}: {e}")
    db.commit()
    print("Done killing stale connections")
finally:
    db.close()