#!/usr/bin/env python3
"""Utility script to manage API keys in the database"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet

from app.core.database import AsyncSessionLocal, init_db
from app.core.security import encrypt_api_key, decrypt_api_key, generate_synthetic_key
from app.models.database import Organization, APIKey, User
from app.config import settings


async def create_organization(session: AsyncSession, name: str) -> Organization:
    """Create a new organization"""
    org = Organization(name=name)
    session.add(org)
    await session.commit()
    await session.refresh(org)
    return org


async def create_api_key(
    session: AsyncSession, 
    org_id: str, 
    openai_key: str, 
    user_id: str = None,
    name: str = None,
    description: str = None
) -> APIKey:
    """Create a new API key mapping"""
    # Generate synthetic key
    synthetic_key = generate_synthetic_key()
    
    # Encrypt the OpenAI key
    encrypted_key = encrypt_api_key(openai_key)
    
    # Verify user exists if provided
    if user_id:
        user_result = await session.execute(
            select(User).where(
                and_(
                    User.id == user_id,
                    User.organization_id == org_id
                )
            )
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            print(f"Error: User not found: {user_id} in organization {org_id}")
            return None
    
    # Create API key record
    api_key = APIKey(
        organization_id=org_id,
        user_id=user_id,
        synthetic_key=synthetic_key,
        openai_api_key=encrypted_key,
        name=name,
        description=description,
        is_active=True
    )
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    return api_key


async def list_organizations(session: AsyncSession):
    """List all organizations"""
    result = await session.execute(select(Organization))
    orgs = result.scalars().all()
    
    if not orgs:
        print("No organizations found.")
        return
    
    print("\nOrganizations:")
    print("-" * 60)
    for org in orgs:
        print(f"ID: {org.id}")
        print(f"Name: {org.name}")
        print(f"Created: {org.created_at}")
        print("-" * 60)


async def list_api_keys(session: AsyncSession, org_id: str = None, user_id: str = None):
    """List API keys, optionally filtered by organization and/or user"""
    query = select(APIKey).join(Organization)
    
    # Apply filters
    if org_id:
        query = query.where(APIKey.organization_id == org_id)
    
    if user_id:
        query = query.where(APIKey.user_id == user_id)
    
    result = await session.execute(query)
    keys = result.scalars().all()
    
    if not keys:
        print("No API keys found.")
        return
    
    print("\nAPI Keys:")
    print("-" * 80)
    for key in keys:
        # Get organization
        org_result = await session.execute(
            select(Organization).where(Organization.id == key.organization_id)
        )
        org = org_result.scalar_one()
        
        # Get user if associated
        user_name = "None"
        if key.user_id:
            user_result = await session.execute(
                select(User).where(User.id == key.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                user_name = user.user_id
        
        print(f"ID: {key.id}")
        print(f"Organization: {org.name} ({org.id})")
        print(f"User: {user_name}")
        print(f"Name: {key.name or 'None'}")
        print(f"Description: {key.description or 'None'}")
        print(f"Synthetic Key: {key.synthetic_key}")
        print(f"Active: {key.is_active}")
        print(f"Created: {key.created_at}")
        print("-" * 80)


async def deactivate_api_key(session: AsyncSession, synthetic_key: str):
    """Deactivate an API key"""
    result = await session.execute(
        select(APIKey).where(APIKey.synthetic_key == synthetic_key)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        print(f"API key not found: {synthetic_key}")
        return
    
    api_key.is_active = False
    await session.commit()
    print(f"API key deactivated: {synthetic_key}")


async def generate_fernet_key():
    """Generate a new Fernet encryption key"""
    key = Fernet.generate_key()
    print("\nGenerated Fernet Encryption Key:")
    print("-" * 60)
    print(key.decode())
    print("-" * 60)
    print("\nAdd this to your .env file as:")
    print(f"ENCRYPTION_KEY={key.decode()}")


async def main():
    parser = argparse.ArgumentParser(
        description="Manage organizations and API keys"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create organization
    create_org_parser = subparsers.add_parser(
        "create-org", help="Create a new organization"
    )
    create_org_parser.add_argument("name", help="Organization name")
    
    # Create API key
    create_key_parser = subparsers.add_parser(
        "create-key", help="Create a new API key mapping"
    )
    create_key_parser.add_argument("org_id", help="Organization ID (UUID)")
    create_key_parser.add_argument("openai_key", help="OpenAI API key to encrypt")
    create_key_parser.add_argument("--user-id", help="User ID to associate with the key (optional)")
    create_key_parser.add_argument("--name", help="Name for the key (optional)")
    create_key_parser.add_argument("--description", help="Description for the key (optional)")
    
    # List organizations
    subparsers.add_parser("list-orgs", help="List all organizations")
    
    # List API keys
    list_keys_parser = subparsers.add_parser(
        "list-keys", help="List API keys"
    )
    list_keys_parser.add_argument(
        "--org-id", help="Filter by organization ID"
    )
    list_keys_parser.add_argument(
        "--user-id", help="Filter by user ID"
    )
    
    # Deactivate API key
    deactivate_parser = subparsers.add_parser(
        "deactivate-key", help="Deactivate an API key"
    )
    deactivate_parser.add_argument("synthetic_key", help="Synthetic API key")
    
    # Generate Fernet key
    subparsers.add_parser("generate-fernet-key", help="Generate a new Fernet encryption key")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Special case for generating Fernet key (doesn't need DB)
    if args.command == "generate-fernet-key":
        await generate_fernet_key()
        return
    
    # Initialize database
    await init_db()
    
    async with AsyncSessionLocal() as session:
        try:
            if args.command == "create-org":
                org = await create_organization(session, args.name)
                print(f"\nOrganization created successfully!")
                print(f"ID: {org.id}")
                print(f"Name: {org.name}")
                
            elif args.command == "create-key":
                # Validate organization ID
                try:
                    uuid.UUID(args.org_id)
                except ValueError:
                    print(f"Error: Invalid UUID format: {args.org_id}")
                    return
                
                # Check if organization exists
                result = await session.execute(
                    select(Organization).where(Organization.id == args.org_id)
                )
                org = result.scalar_one_or_none()
                if not org:
                    print(f"Error: Organization not found: {args.org_id}")
                    return
                
                api_key = await create_api_key(
                    session, 
                    args.org_id, 
                    args.openai_key,
                    user_id=args.user_id,
                    name=args.name,
                    description=args.description
                )
                
                if api_key:
                    print(f"\nAPI key created successfully!")
                    print(f"Organization: {org.name}")
                    if args.user_id:
                        print(f"User ID: {args.user_id}")
                    if args.name:
                        print(f"Name: {args.name}")
                    print(f"Synthetic Key: {api_key.synthetic_key}")
                    print("\nUse this synthetic key in your API requests.")
                
            elif args.command == "list-orgs":
                await list_organizations(session)
                
            elif args.command == "list-keys":
                await list_api_keys(session, args.org_id, args.user_id)
                
            elif args.command == "deactivate-key":
                await deactivate_api_key(session, args.synthetic_key)
                
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(main())
