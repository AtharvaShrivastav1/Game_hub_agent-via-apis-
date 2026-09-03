import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from app.database.session import SessionLocal, init_tables
from app.database.seed_data import reset_and_seed_database, SAMPLE_GAMES

def seed():
    print("Initializing tables...")
    init_tables()
    db = SessionLocal()

    try:
        print(f"Seeding {len(SAMPLE_GAMES)} games and resetting user session data (0 games in library)...")
        reset_and_seed_database(db, reset_user_data=True)
        print("Database seeding completed successfully! Library is fresh with 0 games.")

    except Exception as e:
        db.rollback()
        print(f"Seeding error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
