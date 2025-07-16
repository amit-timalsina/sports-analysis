"""
Auth package.

This package provides functionality for user authentication, authorization, and identity management.

Key components:
- User model: Represents user data and relationships.
- UserIdentity model: Manages various authentication methods for users.
- UserRepositry: Handles database operations for user-related data.
- User Router: Defines api endpoints for user management.

Usage:
    from auth.models import User, UserIdentity
    from auth.repositories import UserRepository
    from auth.routers import user_router


    # Create a new user
    new_user = User(first_name="John", last_name="Doe", email="john.doe@example.com")
    user_repo = UserRepository(session)
    created_user = user_repo.create(new_user)

    # Include user router into your FastAPI application
    app.include_router(user_router)

Note:
Clients of this package should ensure proper database setup and configuration before using the
models and repositories.

The package supports multiple identity providers, currently included Supabase. Extend the
`UserIdentity` model for additional providers as needed.

"""
