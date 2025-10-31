"""
Vector Search Tool for searching the knowledge base
"""

import logging
from typing import Any, List, Dict

logger = logging.getLogger(__name__)


class VectorSearchTool:
    """
    Tool for searching the vector store / knowledge base
    """

    def __init__(self, vector_store: Any):
        """
        Initialize the vector search tool

        Args:
            vector_store: VectorStoreClient instance
        """
        self.vector_store = vector_store
        self.logger = logging.getLogger(__name__)

    def run(self, query: str) -> str:
        """
        Search the knowledge base

        Args:
            query: Search query string

        Returns:
            Formatted search results as string
        """

        try:
            self.logger.info(f"Searching knowledge base for: {query[:100]}...")

            # Perform search
            results = self.vector_store.search_sync(query, limit=5)

            if not results:
                return "No relevant information found in the knowledge base."

            # Format results for better readability
            formatted_results = []
            formatted_results.append(f"I found {len(results)} relevant documents:\n")

            for i, result in enumerate(results, 1):
                doc = result.get("document", {})
                metadata = result.get("metadata", {})
                score = result.get("score", 0)

                source = metadata.get("source", "unknown")
                file_name = metadata.get("file", "")
                sheet_name = metadata.get("sheet", "")

                # Get text and clean it up
                text = doc.get("text", "")

                # For Excel data, format it better
                if source == "excel":
                    # Remove "Unnamed: X: " patterns and format as bullet points
                    lines = text.split(" | ")
                    cleaned_lines = []
                    for line in lines[:5]:  # Show first 5 fields only
                        # Remove "Unnamed: X: " prefix
                        if "Unnamed:" in line:
                            parts = line.split(": ", 1)
                            if len(parts) > 1:
                                cleaned_lines.append(parts[1])
                        else:
                            cleaned_lines.append(line)

                    preview = "\n   • " + "\n   • ".join(cleaned_lines)
                    if len(lines) > 5:
                        preview += f"\n   ... and {len(lines) - 5} more fields"
                else:
                    # For other sources, simple preview
                    preview = text[:300] + "..." if len(text) > 300 else text

                # Build formatted result
                result_parts = [f"\n📄 **Result {i}** (Relevance: {score:.0%})"]

                if file_name:
                    result_parts.append(f"   📁 File: {file_name}")
                if sheet_name:
                    result_parts.append(f"   📊 Sheet: {sheet_name}")

                result_parts.append(f"   Content:{preview}\n")

                formatted_results.append("\n".join(result_parts))

            result_text = "\n".join(formatted_results)

            self.logger.info(f"Search completed: {len(results)} results")

            return result_text

        except Exception as e:
            self.logger.error(f"Error in vector search: {e}")
            return f"Error searching knowledge base: {str(e)}"

    async def arun(self, query: str) -> str:
        """
        Async version of run

        Args:
            query: Search query string

        Returns:
            Formatted search results
        """

        try:
            self.logger.info(f"Async searching for: {query[:100]}...")

            # Perform async search
            results = await self.vector_store.search(query, limit=5)

            if not results:
                return "No relevant information found in the knowledge base."

            # Format results for better readability (same as sync version)
            formatted_results = []
            formatted_results.append(f"I found {len(results)} relevant documents:\n")

            for i, result in enumerate(results, 1):
                doc = result.get("document", {})
                metadata = result.get("metadata", {})
                score = result.get("score", 0)

                source = metadata.get("source", "unknown")
                file_name = metadata.get("file", "")
                sheet_name = metadata.get("sheet", "")

                # Get text and clean it up
                text = doc.get("text", "")

                # For Excel data, format it better
                if source == "excel":
                    # Remove "Unnamed: X: " patterns and format as bullet points
                    lines = text.split(" | ")
                    cleaned_lines = []
                    for line in lines[:5]:  # Show first 5 fields only
                        # Remove "Unnamed: X: " prefix
                        if "Unnamed:" in line:
                            parts = line.split(": ", 1)
                            if len(parts) > 1:
                                cleaned_lines.append(parts[1])
                        else:
                            cleaned_lines.append(line)

                    preview = "\n   • " + "\n   • ".join(cleaned_lines)
                    if len(lines) > 5:
                        preview += f"\n   ... and {len(lines) - 5} more fields"
                else:
                    # For other sources, simple preview
                    preview = text[:300] + "..." if len(text) > 300 else text

                # Build formatted result
                result_parts = [f"\n📄 **Result {i}** (Relevance: {score:.0%})"]

                if file_name:
                    result_parts.append(f"   📁 File: {file_name}")
                if sheet_name:
                    result_parts.append(f"   📊 Sheet: {sheet_name}")

                result_parts.append(f"   Content:{preview}\n")

                formatted_results.append("\n".join(result_parts))

            return "\n".join(formatted_results)

        except Exception as e:
            self.logger.error(f"Error in async vector search: {e}")
            return f"Error searching knowledge base: {str(e)}"
