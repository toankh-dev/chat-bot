"""
Alembic seed command for database seeding.

Usage:
    # From alembic directory
    python -m alembic.seed

    # Or from project root
    python alembic/seed.py
"""

import sys
import os
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import asyncio
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from infrastructure.postgresql.models.user_model import UserModel
from infrastructure.postgresql.models.group_model import Group
from infrastructure.postgresql.models.chatbot_model import ChatbotModel
from infrastructure.postgresql.models.user_group_model import UserGroup
from infrastructure.postgresql.models.group_chatbot import GroupChatbotModel
from infrastructure.postgresql.models.user_chatbot import UserChatbotModel
from infrastructure.postgresql.models.conversation_model import ConversationModel
from core.config import settings


def seed_database():
    """Seed database with test data (sync version for Alembic)."""

    print("="*60)
    print("🌱 ALEMBIC DATABASE SEEDING")
    print("="*60)

    # Create sync engine (Alembic uses sync connections)
    engine = create_engine(settings.postgres_url.replace("+asyncpg", ""))
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check if data already exists
        user_count = session.query(UserModel).count()

        if user_count > 0:
            print(f"\n⚠️  Database already has {user_count} users.")
            print("Seeding skipped to prevent duplicates.")
            print("Use 'python scripts/reset_database.py' to reset and seed.\n")
            return


        print("\n👤 Creating users...")

        # Admin User
        admin_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin_user = UserModel(
            email="admin@kass.dev",
            password_hash=admin_password,
            name="Admin User",
            is_admin=True,
            status="active"
        )
        session.add(admin_user)
        session.flush()
        print(f"✅ Admin user created: {admin_user.email}")

        # Regular User
        user_password = bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        regular_user = UserModel(
            email="user@kass.dev",
            password_hash=user_password,
            name="Regular User",
            is_admin=False,
            status="active"
        )
        session.add(regular_user)
        session.flush()
        print(f"✅ Regular user created: {regular_user.email}")

        # Group
        print("\n👥 Creating group...")
        group = Group(
            name="Engineering Team"
        )
        session.add(group)
        session.flush()
        print(f"✅ Group created: {group.name}")

        # Add users to group
        print("\n🔗 Adding users to group...")
        admin_group_link = UserGroup(
            user_id=admin_user.id,
            group_id=group.id,
            added_by=admin_user.id
        )
        session.add(admin_group_link)

        user_group_link = UserGroup(
            user_id=regular_user.id,
            group_id=group.id,
            added_by=admin_user.id
        )
        session.add(user_group_link)
        session.flush()
        print("✅ Users added to group")

        # Chatbot
        print("\n🤖 Creating chatbot...")

        chatbot = ChatbotModel(
            name="Code Assistant",
            description="AI assistant that helps with code questions using repository knowledge",
            model_id=6,  # claude-3-5-sonnet
            temperature=0.7,
            max_tokens=2048,
            top_p=1.0,
            system_prompt="""You are a helpful code assistant with access to repository documentation and code.
Your role is to:
1. Answer questions about code in the repository
2. Provide clear, accurate explanations
3. Help developers understand codebases
4. Suggest best practices

Always cite specific files or functions when answering questions.""",
            welcome_message="Hi! I'm your Code Assistant. I can help you understand the codebase. What would you like to know?",
            fallback_message="I'm having trouble accessing my knowledge base right now. Please try again in a moment.",
            max_conversation_length=50,
            enable_function_calling=True,
            created_by=admin_user.id,
            status="active"
        )
        session.add(chatbot)
        session.flush()
        print(f"✅ Chatbot created: {chatbot.name}")

        # Link chatbot to group
        print("\n🔗 Linking chatbot to group...")
        group_chatbot = GroupChatbotModel(
            group_id=group.id,
            chatbot_id=chatbot.id,
            assigned_by=admin_user.id,
            assigned_at=datetime.utcnow()
        )
        session.add(group_chatbot)
        session.flush()
        print("✅ Chatbot linked to group")

        # Give users access to chatbot
        print("\n🔗 Giving users access to chatbot...")
        admin_chatbot = UserChatbotModel(
            user_id=admin_user.id,
            chatbot_id=chatbot.id,
            assigned_by=admin_user.id,
            assigned_at=datetime.utcnow()
        )
        session.add(admin_chatbot)

        user_chatbot = UserChatbotModel(
            user_id=regular_user.id,
            chatbot_id=chatbot.id,
            assigned_by=admin_user.id,
            assigned_at=datetime.utcnow()
        )
        session.add(user_chatbot)
        session.flush()
        print("✅ Users granted access to chatbot")

        # Sample conversation
        print("\n💬 Creating sample conversation...")
        conversation = ConversationModel(
            chatbot_id=chatbot.id,
            user_id=regular_user.id,
            title="Getting Started",
            status="active",
            is_active=True,
            message_count=0,
            started_at=datetime.utcnow(),
            last_accessed_at=datetime.utcnow()
        )
        session.add(conversation)
        session.flush()
        print(f"✅ Sample conversation created: {conversation.title}")

        session.commit()

        print("\n" + "="*60)
        print("🎉 Database seeding completed successfully!")
        print("="*60)

        print("\n📋 SEED DATA SUMMARY:")
        print("-" * 60)
        print(f"👤 Admin User:")
        print(f"   Email:    admin@kass.dev")
        print(f"   Password: admin123")
        print(f"   ID:       {admin_user.id}")

        print(f"\n👤 Regular User:")
        print(f"   Email:    user@kass.dev")
        print(f"   Password: user123")
        print(f"   ID:       {regular_user.id}")

        print(f"\n👥 Group:")
        print(f"   Name:     {group.name}")
        print(f"   ID:       {group.id}")

        print(f"\n🤖 Chatbot:")
        print(f"   Name:     {chatbot.name}")
        print(f"   ID:       {chatbot.id}")

        print(f"\n💬 Conversation:")
        print(f"   ID:       {conversation.id}")
        print(f"   Title:    {conversation.title}")

        print("\n" + "="*60)
        print("🚀 Next Steps:")
        print("="*60)
        print("1. Start API server: docker-compose up -d")
        print("2. Access Swagger: http://localhost:8000/docs")
        print("3. Login with: admin@kass.dev / admin123")
        print("="*60 + "\n")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    seed_database()
