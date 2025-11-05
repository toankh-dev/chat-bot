"""Pagination utilities"""

from typing import Dict, Optional


class Paginator:
    """Pagination helper"""

    @staticmethod
    def parse_params(query_params: Optional[Dict] = None) -> tuple[int, int, int]:
        """
        Parse pagination parameters from query string
        Returns: (page, limit, offset)
        """
        params = query_params or {}

        try:
            page = int(params.get('page', 1))
            page = max(1, page)  # Minimum page is 1
        except (ValueError, TypeError):
            page = 1

        try:
            limit = int(params.get('limit', 20))
            limit = min(max(1, limit), 100)  # Between 1 and 100
        except (ValueError, TypeError):
            limit = 20

        offset = (page - 1) * limit

        return page, limit, offset

    @staticmethod
    def create_metadata(total: int, page: int, limit: int) -> Dict:
        """Create pagination metadata"""
        pages = (total + limit - 1) // limit if limit > 0 else 0

        return {
            'page': page,
            'limit': limit,
            'total': total,
            'pages': pages,
            'has_next': page < pages,
            'has_prev': page > 1
        }
