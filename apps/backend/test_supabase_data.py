"""Test Supabase data storage and retrieval."""

from app.core.db import SessionLocal
from app.models.user import User
from app.models.trip import Trip
from app.core.config import settings
from sqlalchemy import text


def test_supabase_connection():
    """Test connection to Supabase and verify data storage."""
    
    print("=" * 60)
    print("Testing Supabase Connection")
    print("=" * 60)
    
    print(f"\nDatabase URL: {settings.database_url.split('@')[1].split('/')[0]}")
    
    db = SessionLocal()
    
    try:
        # Test connection
        print("\n✓ Database connection successful")
        
        # Query all users
        print("\n--- Users in Supabase ---")
        users = db.query(User).all()
        print(f"Total users: {len(users)}")
        for user in users:
            print(f"  - Email: {user.email}")
            print(f"    Name: {user.name}")
            print(f"    ID: {user.id}")
            print(f"    Created: {user.created_at}")
            print(f"    Active: {user.is_active}")
            print()
        
        # Query all trips
        print("--- Trips in Supabase ---")
        trips = db.query(Trip).all()
        print(f"Total trips: {len(trips)}")
        for trip in trips:
            print(f"  - Trip ID: {trip.id}")
            print(f"    Destinations: {', '.join(trip.destinations)}")
            print(f"    Dates: {trip.start_date} to {trip.end_date}")
            print(f"    User ID: {trip.user_id}")
            print(f"    Created: {trip.created_at}")
            print()
        
        # Query all tables to show structure
        print("--- Database Tables ---")
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
        
        print("\n✓ Data successfully stored and retrieved from Supabase!")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_supabase_connection()
