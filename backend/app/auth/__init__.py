"""Authentication and authorization package.

Planned architecture:
Supabase Auth -> FastAPI identity/role validation -> PostgreSQL RLS -> Assignment-based authorization

Roles:
- MOTHER
- ASHA
- ADMIN (Future, server-controlled)

Note: Full authentication is planned for the Authentication/RLS phase.
"""
