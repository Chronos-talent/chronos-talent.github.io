from database import SessionLocal, Job, engine
from sqlalchemy import Column, String, text

# Add category column if it doesn't exist
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE jobs ADD COLUMN category VARCHAR"))
        conn.commit()
        print("✅ Added category column to database!")
except Exception as e:
    print("ℹ️ Category column might already exist:", e)

print("✅ Database update complete!")