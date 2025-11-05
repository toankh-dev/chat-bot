"""Standardized API response builder"""

from typing import Any, Optional, Dict, List
import json
from datetime import datetime
from decimal import Decimal


class APIResponse:
    """Standardized API response builder for Lambda functions"""

    @staticmethod
    def _json_serializer(obj):
        """Custom JSON serializer for special types"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return str(obj)

    @staticmethod
    def success(
        data: Any = None,
        message: Optional[str] = None,
        status_code: int = 200,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Success response"""
        response_body = {
            'success': True,
            'data': data,
            'metadata': {
                'timestamp': datetime.utcnow().isoformat(),
                **(metadata or {})
            }
        }

        if message:
            response_body['message'] = message

        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps(response_body, default=APIResponse._json_serializer)
        }

    @staticmethod
    def error(
        message: str,
        code: str = "ERROR",
        details: Optional[Any] = None,
        status_code: int = 400
    ) -> Dict:
        """Error response"""
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'success': False,
                'error': {
                    'code': code,
                    'message': message,
                    'details': details
                },
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                }
            }, default=APIResponse._json_serializer)
        }

    @staticmethod
    def paginated(
        data: List[Any],
        total: int,
        page: int,
        limit: int,
        message: Optional[str] = None
    ) -> Dict:
        """Paginated response"""
        pages = (total + limit - 1) // limit if limit > 0 else 0

        return APIResponse.success(
            data={
                'items': data,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': pages,
                    'has_next': page < pages,
                    'has_prev': page > 1
                }
            },
            message=message,
            metadata={
                'total_count': total,
                'page': page,
                'limit': limit
            }
        )

    @staticmethod
    def created(data: Any = None, message: str = "Resource created successfully") -> Dict:
        """Created response (201)"""
        return APIResponse.success(data=data, message=message, status_code=201)

    @staticmethod
    def no_content(message: str = "Operation completed successfully") -> Dict:
        """No content response (204)"""
        return {
            'statusCode': 204,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': ''
        }

    @staticmethod
    def unauthorized(message: str = "Unauthorized") -> Dict:
        """Unauthorized response (401)"""
        return APIResponse.error(message, code="UNAUTHORIZED", status_code=401)

    @staticmethod
    def forbidden(message: str = "Forbidden") -> Dict:
        """Forbidden response (403)"""
        return APIResponse.error(message, code="FORBIDDEN", status_code=403)

    @staticmethod
    def not_found(message: str = "Resource not found") -> Dict:
        """Not found response (404)"""
        return APIResponse.error(message, code="NOT_FOUND", status_code=404)

    @staticmethod
    def conflict(message: str = "Resource conflict") -> Dict:
        """Conflict response (409)"""
        return APIResponse.error(message, code="CONFLICT", status_code=409)

    @staticmethod
    def validation_error(message: str, details: Optional[Any] = None) -> Dict:
        """Validation error response (400)"""
        return APIResponse.error(message, code="VALIDATION_ERROR", details=details, status_code=400)

    @staticmethod
    def internal_error(message: str = "Internal server error") -> Dict:
        """Internal server error response (500)"""
        return APIResponse.error(message, code="INTERNAL_ERROR", status_code=500)
