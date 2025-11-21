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

# Add src/ to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from infrastructure.postgresql.models.user_model import UserModel
from infrastructure.postgresql.models.group_model import Group
from infrastructure.postgresql.models.chatbot_model import ChatbotModel
from infrastructure.postgresql.models.user_group_model import UserGroup
from infrastructure.postgresql.models.group_chatbot import GroupChatbotModel
from infrastructure.postgresql.models.user_chatbot import UserChatbotModel
from infrastructure.postgresql.models.conversation_model import ConversationModel
from infrastructure.postgresql.models.knowledge_base_model import KnowledgeBaseModel
from core.config import settings


def seed_database():
    """Seed database with initial data."""

    print("=" * 60)
    print("🌱 ALEMBIC DATABASE SEEDING")
    print("=" * 60)

    engine = create_engine(settings.postgres_url.replace("+asyncpg", ""))
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # ============================================================
        # PART 1: SEED AI MODELS
        # ============================================================
        print("\n🤖 Creating AI models...")

        predefined_models = [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
        ]

        for model_name in predefined_models:
            existing = session.execute(
                text("SELECT id FROM ai_models WHERE name = :name"),
                {"name": model_name}
            ).fetchone()

            if existing:
                print(f"⚠️  Already exists: {model_name}")
                continue

            session.execute(
                text("""
                    INSERT INTO ai_models (name, created_at, updated_at)
                    VALUES (:name, :created_at, :updated_at)
                """),
                {
                    "name": model_name,
                    "created_at": datetime.now(datetime.UTC),
                    "updated_at": datetime.now(datetime.UTC),
                }
            )
            print(f"✅ AI Model created: {model_name}")

        session.flush()

        # Default model = gemini-2.5-flash
        model_flash_id = session.execute(
            text("SELECT id FROM ai_models WHERE name='gemini-2.5-flash'")
        ).scalar()

        if not model_flash_id:
            raise Exception("❌ AI model 'gemini-2.5-flash' not found after seeding!")

        print(f"📌 Default model_id = {model_flash_id}")

        # ============================================================
        # PART 2: CHECK IF USERS EXIST
        # ============================================================
        user_count = session.query(UserModel).count()

        if user_count > 0:
            print(f"\n⚠️  Database already has {user_count} users.")
            print("Seeding skipped to prevent duplicates.")
            print("Use 'python scripts/reset_database.py' to reset and seed.\n")
            return

        # ============================================================
        # PART 3: SEED USERS
        # ============================================================
        print("\n👤 Creating users...")

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

        # ============================================================
        # PART 4: GROUP
        # ============================================================
        print("\n👥 Creating group...")

        group = Group(name="Engineering Team")
        session.add(group)
        session.flush()
        print(f"✅ Group created: {group.name}")

        # Add users to group
        print("\n🔗 Adding users to group...")
        session.add(UserGroup(user_id=admin_user.id, group_id=group.id, added_by=admin_user.id))
        session.add(UserGroup(user_id=regular_user.id, group_id=group.id, added_by=admin_user.id))
        session.flush()
        print("✅ Users added to group")

        # ============================================================
        # PART 5: CREATE CHATBOT
        # ============================================================
        print("\n🤖 Creating chatbot...")

        chatbot = ChatbotModel(
            name="Code Assistant",
            description="AI assistant that helps with code questions using repository knowledge",
            model_id=model_flash_id,  # <-- auto from ai_models
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
        session.add(GroupChatbotModel(
            group_id=group.id,
            chatbot_id=chatbot.id,
            assigned_by=admin_user.id,
            assigned_at=datetime.now(datetime.UTC)
        ))
        session.flush()
        print("✅ Chatbot linked to group")

        # Give users access
        print("\n🔗 Giving users access to chatbot...")
        session.add(UserChatbotModel(
            user_id=admin_user.id,
            chatbot_id=chatbot.id,
            assigned_by=admin_user.id,
            assigned_at=datetime.now(datetime.UTC)
        ))
        session.add(UserChatbotModel(
            user_id=regular_user.id,
            chatbot_id=chatbot.id,
            assigned_by=admin_user.id,
            assigned_at=datetime.now(datetime.UTC)
        ))
        session.flush()
        print("✅ Users granted access")

        # ============================================================
        # PART 5.1: CREATE DEFAULT KNOWLEDGE BASE
        # ============================================================

        print("\n📚 Creating default knowledge base...")

        collection_name = f"chatbot_{chatbot.id}_default_kb"

        default_kb = KnowledgeBaseModel(
            chatbot_id=chatbot.id,
            name="Default Knowledge Base",
            description="Default knowledge base for this chatbot",
            vector_store_type="chromadb",
            vector_store_collection=collection_name,
            vector_store_config=None,
            is_active=True
        )

        session.add(default_kb)
        session.flush()

        print(f"✅ Knowledge Base created: {default_kb.name} (ID={default_kb.id})")
        print(f"📌 Collection: {collection_name}")


        # ============================================================
        # PART 6: SAMPLE CONVERSATION
        # ============================================================
        print("\n💬 Creating sample conversation...")

        conversation = ConversationModel(
            chatbot_id=chatbot.id,
            user_id=regular_user.id,
            title="Getting Started",
            status="active",
            is_active=True,
            message_count=0,
            started_at=datetime.now(datetime.UTC),
            last_accessed_at=datetime.now(datetime.UTC)
        )
        session.add(conversation)
        session.flush()
        print(f"✅ Sample conversation created: {conversation.title}")

        # Commit all
        session.commit()

        # ============================================================
        # SUMMARY
        # ============================================================
        print("\n" + "=" * 60)
        print("🎉 Database seeding completed successfully!")
        print("=" * 60)

        print("\n📋 SEED DATA SUMMARY:")
        print("-" * 60)
        print(f"👤 Admin: admin@kass.dev / admin123 / ID={admin_user.id}")
        print(f"👤 User:  user@kass.dev / user123 / ID={regular_user.id}")
        print(f"\n🤖 Chatbot: {chatbot.name} (model_id={model_flash_id})")
        print(f"👥 Group: {group.name} (ID={group.id})")
        print(f"💬 Conversation: {conversation.title}\n")

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
