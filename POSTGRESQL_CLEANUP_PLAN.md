# PostgreSQL Infrastructure Cleanup Plan

## 🗂️ PROPOSED CLEAN STRUCTURE:

```
infrastructure/postgresql/
├── connection/
│   ├── __init__.py
│   ├── database.py          # DB connection & session management
│   └── base.py              # Base model & config
├── models/
│   ├── __init__.py          # Export all models
│   ├── user.py
│   ├── chatbot.py
│   ├── conversation.py
│   ├── document.py
│   └── message.py
├── repositories/
│   ├── __init__.py
│   ├── user_repository.py
│   ├── chatbot_repository.py
│   ├── conversation_repository.py
│   ├── document_repository.py
│   └── message_repository.py
├── mappers/
│   ├── __init__.py
│   ├── user_mapper.py
│   ├── chatbot_mapper.py
│   ├── conversation_mapper.py
│   ├── document_mapper.py
│   └── message_mapper.py
└── __init__.py              # Clean exports
```

## 🎯 BENEFITS:
✅ Logical grouping by responsibility
✅ Consistent naming (remove _impl suffix)
✅ Complete mapper coverage
✅ Separated connection management
✅ Easier to navigate & maintain
✅ Clear imports/exports

## 🚀 MIGRATION STEPS:
1. Create new structure
2. Move & rename files
3. Update imports
4. Remove old files
5. Test everything

Would you like me to execute this cleanup plan?