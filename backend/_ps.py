from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    r = db.execute(text("SHOW PROCESSLIST")).fetchall()
    print("Active queries:")
    for row in r:
        if row[4] != 'Sleep' and row[4] != 'Daemon':
            print(f"  Id={row[0]}, Command={row[4]}, Time={row[5]}s, State={row[6]}, Info={str(row[7])[:100] if row[7] else 'None'}")
finally:
    db.close()