"""Base repository with common CRUD operations"""

from typing import Optional, List, Dict, Any, TypeVar, Generic
from abc import ABC, abstractmethod
import psycopg2
from psycopg2.extras import RealDictCursor
import os

from ..utils.exceptions import DatabaseError, NotFoundError

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Base repository with CRUD operations"""

    def __init__(self):
        self.table_name = self.get_table_name()

    @abstractmethod
    def get_table_name(self) -> str:
        """Get table name"""
        pass

    @abstractmethod
    def to_model(self, row: Dict) -> T:
        """Convert database row to domain model"""
        pass

    @abstractmethod
    def to_dict(self, model: T) -> Dict:
        """Convert domain model to dict for database"""
        pass

    def get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '5432')),
                database=os.getenv('DB_NAME', 'chatbot'),
                user=os.getenv('DB_USER', 'chatbot'),
                password=os.getenv('DB_PASSWORD', 'chatbot_password'),
                cursor_factory=RealDictCursor
            )
        except Exception as e:
            raise DatabaseError(f"Failed to connect to database: {str(e)}")

    def find_by_id(self, id: int) -> Optional[T]:
        """Find record by ID"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                query = f'SELECT * FROM "{self.table_name}" WHERE id = %s'
                cursor.execute(query, (id,))
                row = cursor.fetchone()

                if row:
                    return self.to_model(dict(row))
                return None
        except Exception as e:
            raise DatabaseError(f"Failed to find record: {str(e)}")
        finally:
            if conn:
                conn.close()

    def find_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = 'id',
        order_dir: str = 'ASC'
    ) -> List[T]:
        """Find all records"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                query = f'SELECT * FROM "{self.table_name}" ORDER BY "{order_by}" {order_dir}'

                if limit:
                    query += f' LIMIT {limit}'
                if offset:
                    query += f' OFFSET {offset}'

                cursor.execute(query)
                rows = cursor.fetchall()

                return [self.to_model(dict(row)) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Failed to find records: {str(e)}")
        finally:
            if conn:
                conn.close()

    def find_by_field(self, field: str, value: Any) -> Optional[T]:
        """Find record by field"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                query = f'SELECT * FROM "{self.table_name}" WHERE "{field}" = %s'
                cursor.execute(query, (value,))
                row = cursor.fetchone()

                if row:
                    return self.to_model(dict(row))
                return None
        except Exception as e:
            raise DatabaseError(f"Failed to find record: {str(e)}")
        finally:
            if conn:
                conn.close()

    def find_many_by_field(
        self,
        field: str,
        value: Any,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """Find multiple records by field"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                query = f'SELECT * FROM "{self.table_name}" WHERE "{field}" = %s'

                if limit:
                    query += f' LIMIT {limit}'
                if offset:
                    query += f' OFFSET {offset}'

                cursor.execute(query, (value,))
                rows = cursor.fetchall()

                return [self.to_model(dict(row)) for row in rows]
        except Exception as e:
            raise DatabaseError(f"Failed to find records: {str(e)}")
        finally:
            if conn:
                conn.close()

    def create(self, model: T) -> T:
        """Create new record"""
        conn = None
        try:
            conn = self.get_connection()
            data = self.to_dict(model)

            # Remove id and timestamp fields
            data.pop('id', None)
            data.pop('created_at', None)
            data.pop('updated_at', None)

            columns = ', '.join(f'"{k}"' for k in data.keys())
            placeholders = ', '.join(['%s'] * len(data))

            query = f'''
                INSERT INTO "{self.table_name}" ({columns})
                VALUES ({placeholders})
                RETURNING *
            '''

            with conn.cursor() as cursor:
                cursor.execute(query, tuple(data.values()))
                row = cursor.fetchone()
                conn.commit()

                return self.to_model(dict(row))
        except Exception as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Failed to create record: {str(e)}")
        finally:
            if conn:
                conn.close()

    def update(self, id: int, model: T) -> T:
        """Update existing record"""
        conn = None
        try:
            conn = self.get_connection()
            data = self.to_dict(model)

            # Remove id and timestamps
            data.pop('id', None)
            data.pop('created_at', None)
            data.pop('updated_at', None)

            set_clause = ', '.join(f'"{k}" = %s' for k in data.keys())
            query = f'''
                UPDATE "{self.table_name}"
                SET {set_clause}, "updated_at" = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING *
            '''

            with conn.cursor() as cursor:
                cursor.execute(query, (*data.values(), id))
                row = cursor.fetchone()

                if not row:
                    raise NotFoundError(f"Record with id {id} not found")

                conn.commit()
                return self.to_model(dict(row))
        except NotFoundError:
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Failed to update record: {str(e)}")
        finally:
            if conn:
                conn.close()

    def delete(self, id: int) -> bool:
        """Delete record"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                query = f'DELETE FROM "{self.table_name}" WHERE id = %s'
                cursor.execute(query, (id,))
                deleted = cursor.rowcount > 0
                conn.commit()
                return deleted
        except Exception as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Failed to delete record: {str(e)}")
        finally:
            if conn:
                conn.close()

    def count(self, where_clause: str = '', params: tuple = ()) -> int:
        """Count records"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                query = f'SELECT COUNT(*) as count FROM "{self.table_name}"'

                if where_clause:
                    query += f' WHERE {where_clause}'

                cursor.execute(query, params)
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            raise DatabaseError(f"Failed to count records: {str(e)}")
        finally:
            if conn:
                conn.close()

    def exists(self, field: str, value: Any, exclude_id: Optional[int] = None) -> bool:
        """Check if record exists"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                query = f'SELECT EXISTS(SELECT 1 FROM "{self.table_name}" WHERE "{field}" = %s'
                params = [value]

                if exclude_id:
                    query += ' AND id != %s'
                    params.append(exclude_id)

                query += ') as exists'

                cursor.execute(query, params)
                result = cursor.fetchone()
                return result['exists'] if result else False
        except Exception as e:
            raise DatabaseError(f"Failed to check existence: {str(e)}")
        finally:
            if conn:
                conn.close()
