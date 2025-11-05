"""User repository"""

from typing import Optional, List, Dict
from datetime import datetime

from .base import BaseRepository
from ..models.domain.user import User, UserStatus, UserRole
from ..utils.exceptions import ConflictError


class UserRepository(BaseRepository[User]):
    """Repository for user operations"""

    def get_table_name(self) -> str:
        return "users"

    def to_model(self, row: Dict) -> User:
        """Convert database row to User model"""
        return User(
            id=row.get('id'),
            group_id=row.get('group_id'),
            email=row['email'],
            name=row['name'],
            is_admin=row.get('is_admin', False),
            status=UserStatus(row.get('status', 'active')),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            roles=[]  # Roles will be loaded separately
        )

    def to_dict(self, model: User) -> Dict:
        """Convert User model to dict"""
        data = {
            'email': model.email,
            'name': model.name,
            'is_admin': model.is_admin,
            'status': model.status.value,
        }

        if model.id:
            data['id'] = model.id
        if model.group_id:
            data['group_id'] = model.group_id

        return data

    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        return self.find_by_field('email', email)

    def find_by_group(
        self,
        group_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[User]:
        """Find users by group"""
        return self.find_many_by_field('group_id', group_id, limit, offset)

    def find_active_users(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[User]:
        """Find active users"""
        return self.find_many_by_field('status', UserStatus.ACTIVE.value, limit, offset)

    def create_user(self, user: User) -> User:
        """Create new user with validation"""
        # Check if email already exists
        if self.exists('email', user.email):
            raise ConflictError(f"User with email {user.email} already exists")

        return self.create(user)

    def update_user(self, user_id: int, user: User) -> User:
        """Update user with validation"""
        # Check if email is being changed and already exists
        if user.email:
            if self.exists('email', user.email, exclude_id=user_id):
                raise ConflictError(f"User with email {user.email} already exists")

        return self.update(user_id, user)

    def update_status(self, user_id: int, status: UserStatus) -> User:
        """Update user status"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                query = '''
                    UPDATE "users"
                    SET "status" = %s, "updated_at" = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING *
                '''
                cursor.execute(query, (status.value, user_id))
                row = cursor.fetchone()

                if not row:
                    from ..utils.exceptions import NotFoundError
                    raise NotFoundError(f"User with id {user_id} not found")

                conn.commit()
                return self.to_model(dict(row))
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def count_by_group(self, group_id: int) -> int:
        """Count users in group"""
        return self.count('group_id = %s', (group_id,))

    def count_by_status(self, status: UserStatus) -> int:
        """Count users by status"""
        return self.count('status = %s', (status.value,))

    def search_users(
        self,
        query: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[User]:
        """Search users by name or email"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                sql = '''
                    SELECT * FROM "users"
                    WHERE "name" ILIKE %s OR "email" ILIKE %s
                    ORDER BY "name" ASC
                '''

                if limit:
                    sql += f' LIMIT {limit}'
                if offset:
                    sql += f' OFFSET {offset}'

                search_pattern = f'%{query}%'
                cursor.execute(sql, (search_pattern, search_pattern))
                rows = cursor.fetchall()

                return [self.to_model(dict(row)) for row in rows]
        except Exception as e:
            from ..utils.exceptions import DatabaseError
            raise DatabaseError(f"Failed to search users: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_user_with_roles(self, user_id: int) -> Optional[User]:
        """Get user with their roles"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Get user
                user_query = 'SELECT * FROM "users" WHERE id = %s'
                cursor.execute(user_query, (user_id,))
                user_row = cursor.fetchone()

                if not user_row:
                    return None

                user = self.to_model(dict(user_row))

                # Get user roles
                roles_query = '''
                    SELECT r."name"
                    FROM "user_roles" ur
                    JOIN "roles" r ON ur.role_id = r.id
                    WHERE ur.user_id = %s
                '''
                cursor.execute(roles_query, (user_id,))
                role_rows = cursor.fetchall()

                user.roles = [UserRole(row['name']) for row in role_rows]

                return user
        except Exception as e:
            from ..utils.exceptions import DatabaseError
            raise DatabaseError(f"Failed to get user with roles: {str(e)}")
        finally:
            if conn:
                conn.close()

    def assign_role(self, user_id: int, role_name: str) -> bool:
        """Assign role to user"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Get role id
                cursor.execute('SELECT id FROM "roles" WHERE "name" = %s', (role_name,))
                role_row = cursor.fetchone()

                if not role_row:
                    from ..utils.exceptions import NotFoundError
                    raise NotFoundError(f"Role {role_name} not found")

                # Check if already assigned
                cursor.execute(
                    'SELECT 1 FROM "user_roles" WHERE user_id = %s AND role_id = %s',
                    (user_id, role_row['id'])
                )

                if cursor.fetchone():
                    return False  # Already assigned

                # Assign role
                cursor.execute(
                    'INSERT INTO "user_roles" (user_id, role_id) VALUES (%s, %s)',
                    (user_id, role_row['id'])
                )

                conn.commit()
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            from ..utils.exceptions import DatabaseError
            raise DatabaseError(f"Failed to assign role: {str(e)}")
        finally:
            if conn:
                conn.close()

    def remove_role(self, user_id: int, role_name: str) -> bool:
        """Remove role from user"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Get role id
                cursor.execute('SELECT id FROM "roles" WHERE "name" = %s', (role_name,))
                role_row = cursor.fetchone()

                if not role_row:
                    return False

                # Remove role
                cursor.execute(
                    'DELETE FROM "user_roles" WHERE user_id = %s AND role_id = %s',
                    (user_id, role_row['id'])
                )

                deleted = cursor.rowcount > 0
                conn.commit()
                return deleted
        except Exception as e:
            if conn:
                conn.rollback()
            from ..utils.exceptions import DatabaseError
            raise DatabaseError(f"Failed to remove role: {str(e)}")
        finally:
            if conn:
                conn.close()
