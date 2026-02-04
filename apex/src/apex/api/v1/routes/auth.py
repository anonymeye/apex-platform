"""Authentication endpoints."""

from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apex.api.v1.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    SwitchOrgRequest,
    TokenResponse,
    UserResponse,
)
from apex.api.dependencies import get_current_user_token
from apex.core.database import get_db
from apex.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    get_role_permissions,
    verify_password,
)
from apex.models.user import Organization, OrganizationMember, User

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_current_user(
    token: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    token_data = decode_access_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # Get user from database
    result = await db.execute(select(User).where(User.id == UUID(token_data.sub)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user and optionally create an organization."""
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=request.email,
        name=request.name,
        password_hash=get_password_hash(request.password),
        is_active=True,
        is_super_admin=False,
    )
    db.add(user)
    await db.flush()  # Get user.id

    # Create organization if name provided
    org_name = request.organization_name or f"{request.name or 'My'} Organization"
    org_slug = org_name.lower().replace(" ", "-") + f"-{uuid4().hex[:8]}"

    organization = Organization(
        name=org_name,
        slug=org_slug,
        subscription_tier="free",
    )
    db.add(organization)
    await db.flush()  # Get organization.id

    # Add user as org_admin to the organization
    org_member = OrganizationMember(
        user_id=user.id,
        organization_id=organization.id,
        role="org_admin",
        is_active=True,
    )
    db.add(org_member)

    await db.commit()

    # Get all organizations user belongs to
    result = await db.execute(
        select(OrganizationMember, Organization)
        .join(Organization)
        .where(OrganizationMember.user_id == user.id, OrganizationMember.is_active == True)
    )
    memberships = result.all()

    orgs = [
        {"id": str(member.organization.id), "name": member.organization.name, "role": member.role}
        for member, org in memberships
    ]

    # Get permissions for role
    permissions = get_role_permissions("org_admin")

    # Create JWT token
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        name=user.name,
        is_super_admin=user.is_super_admin,
        org_id=organization.id,
        org_role="org_admin",
        permissions=permissions,
        orgs=orgs,
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            is_super_admin=user.is_super_admin,
            current_org_id=str(organization.id),
            current_org_name=organization.name,
            current_role="org_admin",
            permissions=permissions,
            organizations=[
                {"id": str(org["id"]), "name": org["name"], "role": org["role"]}
                for org in orgs
            ],
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return JWT token."""
    # Get user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Get user's active organization memberships
    result = await db.execute(
        select(OrganizationMember, Organization)
        .join(Organization)
        .where(OrganizationMember.user_id == user.id, OrganizationMember.is_active == True)
        .order_by(OrganizationMember.created_at)
    )
    memberships = result.all()

    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no active organization memberships",
        )

    # Use first organization as default (or most recent)
    org_member, organization = memberships[0]

    # Get all organizations for token
    orgs = [
        {"id": str(org.id), "name": org.name, "role": member.role}
        for member, org in memberships
    ]

    # Get permissions for role
    permissions = get_role_permissions(org_member.role)
    if user.is_super_admin:
        permissions = ["*"]

    # Create JWT token
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        name=user.name,
        is_super_admin=user.is_super_admin,
        org_id=organization.id,
        org_role=org_member.role,
        permissions=permissions,
        orgs=orgs,
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            is_super_admin=user.is_super_admin,
            current_org_id=str(organization.id),
            current_org_name=organization.name,
            current_role=org_member.role,
            permissions=permissions,
            organizations=orgs,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user information."""
    # Get user's active organization memberships
    result = await db.execute(
        select(OrganizationMember, Organization)
        .join(Organization)
        .where(OrganizationMember.user_id == current_user.id, OrganizationMember.is_active == True)
    )
    memberships = result.all()

    orgs = [
        {"id": str(org.id), "name": org.name, "role": member.role}
        for member, org in memberships
    ]

    # Get current organization from token (would need to extract from token)
    # For now, use first org
    if memberships:
        org_member, organization = memberships[0]
        permissions = get_role_permissions(org_member.role)
        if current_user.is_super_admin:
            permissions = ["*"]

        return UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            name=current_user.name,
            is_super_admin=current_user.is_super_admin,
            current_org_id=str(organization.id),
            current_org_name=organization.name,
            current_role=org_member.role,
            permissions=permissions,
            organizations=orgs,
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User has no active organization memberships",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Clear conversation state for the current user (e.g. on logout)."""
    from apex.core.config import settings
    from apex.storage.conversation_state_store import ConversationStateStore

    if hasattr(request.app.state, "redis") and request.app.state.redis:
        store = ConversationStateStore(
            redis=request.app.state.redis,
            ttl_seconds=settings.conversation_state_ttl_seconds,
        )
        await store.delete_all_for_user(current_user.id)
    return None


@router.post("/switch-org", response_model=TokenResponse)
async def switch_organization(
    request: SwitchOrgRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Switch active organization and return new token."""
    # Verify user is member of requested organization
    result = await db.execute(
        select(OrganizationMember, Organization)
        .join(Organization)
        .where(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.organization_id == UUID(request.org_id),
            OrganizationMember.is_active == True,
        )
    )
    membership = result.first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this organization",
        )

    org_member, organization = membership

    # Get all organizations for token
    result = await db.execute(
        select(OrganizationMember, Organization)
        .join(Organization)
        .where(OrganizationMember.user_id == current_user.id, OrganizationMember.is_active == True)
    )
    memberships = result.all()

    orgs = [
        {"id": str(org.id), "name": org.name, "role": member.role}
        for member, org in memberships
    ]

    # Get permissions for role
    permissions = get_role_permissions(org_member.role)
    if current_user.is_super_admin:
        permissions = ["*"]

    # Create new JWT token with updated org context
    access_token = create_access_token(
        user_id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        is_super_admin=current_user.is_super_admin,
        org_id=organization.id,
        org_role=org_member.role,
        permissions=permissions,
        orgs=orgs,
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            name=current_user.name,
            is_super_admin=current_user.is_super_admin,
            current_org_id=str(organization.id),
            current_org_name=organization.name,
            current_role=org_member.role,
            permissions=permissions,
            organizations=orgs,
        ),
    )
