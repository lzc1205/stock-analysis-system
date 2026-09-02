from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text("KILL 128"))
    db.commit()
    print("Killed 128")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()