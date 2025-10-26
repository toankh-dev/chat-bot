"""
Add sample data to ChromaDB for testing the chatbot
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

import asyncio
import requests
from datetime import datetime

# Sample project data
SAMPLE_DOCUMENTS = [
    {
        "id": "project_status_001",
        "content": "Project Alpha is currently in development phase. We have completed 60% of the backend implementation and 40% of the frontend. The team consists of 5 developers and 2 designers. Expected completion date is December 2025.",
        "metadata": {
            "source": "project_updates",
            "type": "status",
            "project": "Alpha",
            "date": "2025-10-20",
            "author": "Project Manager"
        }
    },
    {
        "id": "bug_report_001",
        "content": "Bug Report #123: Login timeout issue. Users are experiencing timeout errors when trying to log in during peak hours. The issue seems to be related to database connection pooling. Priority: High. Status: In Progress.",
        "metadata": {
            "source": "bug_tracker",
            "type": "bug",
            "severity": "high",
            "status": "in_progress",
            "date": "2025-10-22"
        }
    },
    {
        "id": "bug_report_002",
        "content": "Bug Report #124: Image upload fails for files larger than 5MB. The issue is caused by incorrect NGINX configuration. Priority: Medium. Status: Fixed.",
        "metadata": {
            "source": "bug_tracker",
            "type": "bug",
            "severity": "medium",
            "status": "fixed",
            "date": "2025-10-21"
        }
    },
    {
        "id": "feature_request_001",
        "content": "Feature Request #45: Add dark mode support to the application. Users have requested the ability to switch between light and dark themes. This feature will improve accessibility and user experience.",
        "metadata": {
            "source": "feature_requests",
            "type": "feature",
            "status": "planned",
            "date": "2025-10-18"
        }
    },
    {
        "id": "team_update_001",
        "content": "Team Update: We hired 2 new backend developers this week. They will be working on the API optimization and microservices architecture. Welcome John and Sarah to the team!",
        "metadata": {
            "source": "team_updates",
            "type": "announcement",
            "date": "2025-10-19"
        }
    },
    {
        "id": "deployment_001",
        "content": "Deployment Notice: Version 2.1.0 was successfully deployed to production on October 23, 2025. This release includes bug fixes, performance improvements, and new authentication features.",
        "metadata": {
            "source": "deployments",
            "type": "deployment",
            "version": "2.1.0",
            "date": "2025-10-23"
        }
    },
    {
        "id": "code_review_001",
        "content": "Code Review for PR #456: The authentication refactoring looks good overall. Some suggestions: 1) Add more unit tests for edge cases, 2) Consider using async/await for database calls, 3) Update the API documentation. Approved with minor changes.",
        "metadata": {
            "source": "code_reviews",
            "type": "review",
            "pr_number": "456",
            "status": "approved",
            "date": "2025-10-24"
        }
    },
    {
        "id": "meeting_notes_001",
        "content": "Sprint Planning Meeting Notes (Oct 25, 2025): Discussed priorities for the next sprint. Focus areas: 1) Fix critical bugs in payment system, 2) Implement user analytics dashboard, 3) Optimize database queries. Sprint duration: 2 weeks.",
        "metadata": {
            "source": "meetings",
            "type": "notes",
            "meeting_type": "sprint_planning",
            "date": "2025-10-25"
        }
    }
]


def get_embeddings(texts):
    """Get embeddings from the embedding service"""
    response = requests.post(
        "http://localhost:8002/embed",
        json={"texts": texts},
        timeout=30
    )

    if response.status_code == 200:
        return response.json()["embeddings"]
    else:
        raise Exception(f"Embedding service error: {response.status_code}")


def add_to_chromadb(documents):
    """Add documents to ChromaDB"""
    import chromadb
    from chromadb.config import Settings

    # Connect to ChromaDB (v0.4.24 API)
    client = chromadb.Client(Settings(
        chroma_api_impl="rest",
        chroma_server_host="localhost",
        chroma_server_http_port="8001"
    ))

    # Get or create collection
    collection = client.get_or_create_collection(
        name="chatbot_knowledge",
        metadata={"description": "Knowledge base for chatbot"}
    )

    print(f"Adding {len(documents)} documents to ChromaDB...")

    # Extract texts for embedding
    texts = [doc["content"] for doc in documents]
    ids = [doc["id"] for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]

    # Get embeddings
    print("Generating embeddings...")
    embeddings = get_embeddings(texts)

    # Add to collection
    print("Storing in ChromaDB...")
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    print(f"Successfully added {len(documents)} documents!")
    print(f"Total documents in collection: {collection.count()}")

    # Test query
    print("\nTesting vector search...")
    test_query = "What bugs are currently being worked on?"
    test_embedding = get_embeddings([test_query])[0]

    results = collection.query(
        query_embeddings=[test_embedding],
        n_results=3
    )

    print(f"\nQuery: '{test_query}'")
    print(f"Results:")
    for i, doc in enumerate(results['documents'][0]):
        print(f"\n{i+1}. {doc[:100]}...")


if __name__ == "__main__":
    print("Adding sample data to ChromaDB for testing...\n")

    try:
        add_to_chromadb(SAMPLE_DOCUMENTS)

        print("\n" + "="*60)
        print("Sample data added successfully!")
        print("="*60)
        print("\nYou can now test the chatbot with queries like:")
        print("  - 'What is the status of Project Alpha?'")
        print("  - 'Show me the recent bugs'")
        print("  - 'What features are planned?'")
        print("  - 'Tell me about recent deployments'")
        print("  - 'Summarize the sprint planning meeting'")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
