#!/usr/bin/env python3
"""Utility script to manage users in the database"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, init_db
from app.models.database import Organization, User
from app.services.user_service import UserService


async def list_users(session: AsyncSession, org_id: str = None):
    """List users, optionally filtered by organization"""
    user_service = UserService(session)
    
    if not org_id:
        # List all organizations first
        result = await session.execute(select(Organization))
        orgs = result.scalars().all()
        
        if not orgs:
            print("No organizations found.")
            return
        
        print("\nUsers by Organization:")
        print("=" * 80)
        
        for org in orgs:
            print(f"Organization: {org.name} ({org.id})")
            print("-" * 80)
            
            users = await user_service.get_users(str(org.id))
            
            if not users:
                print("  No users found.")
            else:
                for user in users:
                    print(f"  ID: {user.id}")
                    print(f"  User ID: {user.user_id}")
                    print(f"  Created: {user.created_at}")
                    print("  " + "-" * 76)
            
            print()
    else:
        # Check if organization exists
        org_result = await session.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = org_result.scalar_one_or_none()
        
        if not org:
            print(f"Error: Organization not found: {org_id}")
            return
        
        print(f"\nUsers for Organization: {org.name} ({org.id})")
        print("-" * 80)
        
        users = await user_service.get_users(org_id)
        
        if not users:
            print("No users found.")
        else:
            for user in users:
                print(f"ID: {user.id}")
                print(f"User ID: {user.user_id}")
                print(f"Created: {user.created_at}")
                print("-" * 80)


async def create_user(session: AsyncSession, org_id: str, user_id: str):
    """Create a new user"""
    user_service = UserService(session)
    
    # Check if organization exists
    org_result = await session.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = org_result.scalar_one_or_none()
    
    if not org:
        print(f"Error: Organization not found: {org_id}")
        return
    
    # Create user
    user = await user_service.create_user(org_id, user_id)
    
    if user:
        print(f"\nUser created successfully!")
        print(f"Organization: {org.name}")
        print(f"User ID: {user.user_id}")
        print(f"Internal ID: {user.id}")
    else:
        print(f"Error creating user.")


async def delete_user(session: AsyncSession, user_id: str):
    """Delete a user"""
    user_service = UserService(session)
    
    # Get the user
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        print(f"Error: User not found: {user_id}")
        return
    
    # Get organization
    org_result = await session.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = org_result.scalar_one_or_none()
    
    # Delete user
    success = await user_service.delete_user(user_id)
    
    if success:
        print(f"\nUser deleted successfully!")
        print(f"Organization: {org.name if org else 'Unknown'}")
        print(f"User ID: {user.user_id}")
    else:
        print(f"Error deleting user.")


async def main():
    parser = argparse.ArgumentParser(
        description="Manage users"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create user
    create_user_parser = subparsers.add_parser(
        "create-user", help="Create a new user"
    )
    create_user_parser.add_argument("org_id", help="Organization ID (UUID)")
    create_user_parser.add_argument("user_id", help="External user ID")
    
    # List users
    list_users_parser = subparsers.add_parser(
        "list-users", help="List users"
    )
    list_users_parser.add_argument(
        "--org-id", help="Filter by organization ID"
    )
    
    # Delete user
    delete_user_parser = subparsers.add_parser(
        "delete-user", help="Delete a user"
    )
    delete_user_parser.add_argument("user_id", help="User ID (UUID)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize database
    await init_db()
    
    async with AsyncSessionLocal() as session:
        try:
            if args.command == "create-user":
                # Validate organization ID
                try:
                    uuid.UUID(args.org_id)
                except ValueError:
                    print(f"Error: Invalid UUID format: {args.org_id}")
                    return
                
                await create_user(session, args.org_id, args.user_id)
                
            elif args.command == "list-users":
                org_id = None
                if args.org_id:
                    try:
                        uuid.UUID(args.org_id)
                        org_id = args.org_id
                    except ValueError:
                        print(f"Error: Invalid UUID format: {args.org_id}")
                        return
                
                await list_users(session, org_id)
                
            elif args.command == "delete-user":
                # Validate user ID
                try:
                    uuid.UUID(args.user_id)
                except ValueError:
                    print(f"Error: Invalid UUID format: {args.user_id}")
                    return
                
                await delete_user(session, args.user_id)
                
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(main())
