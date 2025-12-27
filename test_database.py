#!/usr/bin/env python3
"""
Test PostgreSQL + pgVector Setup
Verifies database connection, tables, and basic operations
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_info(text):
    print(f"{BLUE}ℹ{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def test_database():
    print("\n" + "="*60)
    print("DATABASE CONNECTION TEST".center(60))
    print("="*60 + "\n")
    
    # Load .env file
    env_path = Path('.env')
    if not env_path.exists():
        print_error(".env file not found!")
        return False
    
    load_dotenv(dotenv_path=env_path)
    
    # Get DATABASE_URL
    database_url = os.getenv('DATABASE_URL', '')
    
    if not database_url:
        print_error("DATABASE_URL not set in .env file")
        print_info("Add: DATABASE_URL=postgresql://postgres:password@localhost:5432/kuapa_ai")
        return False
    
    print_success(f"Database URL configured")
    
    # Test SQLAlchemy import
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
    except ImportError:
        print_error("SQLAlchemy not installed")
        print_info("Install: pip install sqlalchemy psycopg2-binary pgvector")
        return False
    
    # Test connection
    try:
        print_info("Connecting to PostgreSQL...")
        engine = create_engine(database_url, echo=False)
        
        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print_success("Connected to PostgreSQL successfully")
            print(f"  Version: {version[:50]}...")
            
            # Get current database
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print_success(f"Database: {db_name}")
            
            # Check pgVector extension
            result = conn.execute(text(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            ))
            has_pgvector = result.fetchone()[0]
            
            if has_pgvector:
                print_success("pgVector extension installed")
            else:
                print_warning("pgVector extension not installed (optional - for semantic search)")
                print_info("Database will work fine without it. Can add later if needed.")
            
            # Check if tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print_success("Tables created successfully")
                print("\n" + BLUE + "Tables found:" + RESET)
                for table in tables:
                    print(f"  • {table}")
            else:
                print_warning("No tables found - run migrations:")
                print_info("psql -U postgres -d kuapa_ai -f db/migrations_no_vector.sql")
                return False
            
            # Test creating a user
            print("\n" + BLUE + "Testing database operations..." + RESET)
            
            from api.database import init_db, get_db_context
            from api.user_service import UserService
            
            # Initialize database
            if not init_db():
                print_error("Failed to initialize database")
                return False
            
            print_success("Database initialized")
            
            # Test user operations
            with get_db_context() as db:
                if db is None:
                    print_error("Failed to get database session")
                    return False
                
                # Create test user
                test_phone = "+233000000000"
                user = UserService.get_or_create_user(db, test_phone, "Test User")
                print_success(f"Test user created: {user.phone_number}")
                
                # Create conversation
                conversation = UserService.get_or_create_conversation(db, user.id)
                print_success(f"Test conversation created")
                
                # Save message
                message = UserService.save_message(
                    db=db,
                    user_id=user.id,
                    conversation_id=conversation.id,
                    content="Test message for database verification",
                    direction="incoming",
                    message_type="text",
                    language="en"
                )
                print_success(f"Test message saved")
                
                # Get user stats
                stats = UserService.get_user_stats(db, user.id)
                print_success("User stats retrieved:")
                print(f"  • Total messages: {stats.get('total_messages', 0)}")
                print(f"  • Total conversations: {stats.get('total_conversations', 0)}")
            
            print("\n" + "="*60)
            print(f"{GREEN}SUCCESS - DATABASE READY!{RESET}".center(60))
            print("="*60 + "\n")
            
            print(f"{BLUE}Database features enabled:{RESET}")
            print("  ✓ User profiles")
            print("  ✓ Conversation history")
            print("  ✓ Message storage")
            print("  ✓ Language preferences")
            print("  ✓ Analytics tracking")
            if has_pgvector:
                print("  ✓ Semantic search (pgVector)")
            else:
                print("  ○ Semantic search (needs pgVector)")
            
            print(f"\n{BLUE}Next steps:{RESET}")
            print("1. Restart backend: python -m uvicorn api.main:app --reload")
            print("2. Test user registration via WhatsApp")
            print("3. Messages will now be saved to database\n")
            
            return True
            
    except Exception as e:
        print_error(f"Database connection failed: {str(e)}")
        print("\n" + YELLOW + "Common issues:" + RESET)
        print("1. PostgreSQL not running - check services.msc")
        print("2. Wrong password in DATABASE_URL")
        print("3. Database 'kuapa_ai' doesn't exist - create it first")
        print("4. pgVector extension not installed")
        print("\n" + BLUE + "See POSTGRESQL_SETUP.md for detailed setup guide" + RESET + "\n")
        return False

if __name__ == "__main__":
    try:
        success = test_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
