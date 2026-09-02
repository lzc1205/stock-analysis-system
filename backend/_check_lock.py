from app.utils.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    r = db.execute(text("SHOW PROCESSLIST")).fetchall()
    print("MySQL processlist:")
    for row in r:
        print(f"  Id={row[0]}, User={row[1]}, Host={row[2]}, DB={row[3]}, Command={row[4]}, Time={row[5]}, State={row[6]}")
    
    r2 = db.execute(text("SHOW ENGINE INNODB STATUS")).fetchone()
    # Just show the lock section
    status = r2[2] if len(r2) > 2 else ""
    lines = status.split('\n')
    in_locks = False
    for line in lines:
        if 'LATEST DETECTED DEADLOCK' in line or 'TRANSACTIONS' in line:
            in_locks = True
        if in_locks:
            print(line)
            if '---' in line and 'TRANSACTIONS' not in line:
                if in_locks:
                    pass
finally:
    db.close()