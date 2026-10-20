"""User profile, degree graph, experience, education, and skills API router (API-006 through API-017)."""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import (
    UserNotFoundException,
    ResourceNotFoundException,
    EndDateBeforeStartDateException,
)
from app.api.deps import get_current_user
from app.models.schema import (
    User, Profile, Experience, Education, Skill, UserSkill
)
from app.schemas.contracts import (
    ProfileDetailDTO,
    ProfileDTO,
    ProfileUpdateDTO,
    UserSummaryDTO,
    ExperienceDTO,
    ExperienceCreateDTO,
    ExperienceUpdateDTO,
    EducationDTO,
    EducationCreateDTO,
    EducationUpdateDTO,
    SkillDTO,
    UserSkillAddDTO,
)
from app.services.graph_service import GraphService

router = APIRouter(tags=["Users & Profiles"])


@router.get("/users/me/profile", response_model=ProfileDTO, status_code=status.HTTP_200_OK)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convenience endpoint to retrieve authenticated user's profile."""
    if not current_user.profile:
        raise ResourceNotFoundException("Profile not found for this user.")
    return ProfileDTO.model_validate(current_user.profile)


@router.patch("/users/me/profile", response_model=ProfileDTO, status_code=status.HTTP_200_OK)
async def update_my_profile(
    body: ProfileUpdateDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-007: Update authenticated user's professional profile attributes."""
    stmt = select(Profile).where(Profile.user_id == current_user.id)
    res = await db.execute(stmt)
    profile = res.scalars().first()
    if not profile:
        profile = Profile(
            id=f"prf_{current_user.id}",
            user_id=current_user.id,
            headline=body.headline or "Professional",
            location=body.location or "Global",
        )
        db.add(profile)

    if body.headline is not None:
        profile.headline = body.headline
    if body.bio is not None:
        profile.bio = body.bio
    if body.location is not None:
        profile.location = body.location
    if body.avatar_url is not None:
        profile.avatar_url = body.avatar_url

    await db.commit()
    await db.refresh(profile)
    return ProfileDTO.model_validate(profile)


@router.get("/users/{user_id}", response_model=ProfileDetailDTO, status_code=status.HTTP_200_OK)
async def get_user_profile_detail(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-006: Retrieve user profile detail with degree badge (1st/2nd/3rd+) and mutuals."""
    target_id = current_user.id if user_id == "me" else user_id

    stmt = (
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.experiences),
            selectinload(User.educations),
            selectinload(User.user_skills).selectinload(UserSkill.skill),
        )
        .where(User.id == target_id, User.is_active == True)
    )
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user or not user.profile:
        raise UserNotFoundException(f"User '{target_id}' was not found.")

    (
        degree,
        mutual_count,
        mutuals,
        conn_status,
        viewer_initiated,
        active_conn_id,
    ) = await GraphService.evaluate_degree_and_connection(current_user.id, target_id, db)

    experiences = [
        ExperienceDTO.model_validate(exp) for exp in user.experiences
    ]
    educations = [
        EducationDTO.model_validate(edu) for edu in user.educations
    ]
    skills = [
        SkillDTO(id=us.skill.id, name=us.skill.name, category=us.skill.category)
        for us in user.user_skills
        if us.skill
    ]

    return ProfileDetailDTO(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        profile=ProfileDTO.model_validate(user.profile),
        degree=degree,
        mutual_connections_count=mutual_count,
        mutual_connections_preview=mutuals[:5],
        experiences=experiences,
        educations=educations,
        skills=skills,
        connection_status_with_viewer=conn_status,
        viewer_initiated_connection=viewer_initiated,
        active_connection_id=active_conn_id,
    )


@router.get("/users/{user_id}/mutuals", response_model=List[UserSummaryDTO], status_code=status.HTTP_200_OK)
async def get_mutual_connections(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-008: List mutual 1st-degree connections between current user and target user."""
    return await GraphService.get_mutual_connections(current_user.id, user_id, db)


# ==============================================================================
# WORK EXPERIENCES
# ==============================================================================

@router.post("/users/me/experiences", response_model=ExperienceDTO, status_code=status.HTTP_201_CREATED)
async def add_experience(
    body: ExperienceCreateDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-009: Add a work experience entry to authenticated user's profile."""
    exp_id = f"exp_{uuid.uuid4().hex[:12]}"
    exp = Experience(
        id=exp_id,
        user_id=current_user.id,
        company=body.company,
        title=body.title,
        location=body.location,
        start_date=body.start_date,
        end_date=None if body.is_current else body.end_date,
        is_current=body.is_current,
        description=body.description,
    )
    db.add(exp)
    await db.commit()
    await db.refresh(exp)
    return ExperienceDTO.model_validate(exp)


@router.put("/users/me/experiences/{experience_id}", response_model=ExperienceDTO, status_code=status.HTTP_200_OK)
async def update_experience(
    experience_id: str,
    body: ExperienceUpdateDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-010: Update an existing work experience entry."""
    stmt = select(Experience).where(
        Experience.id == experience_id,
        Experience.user_id == current_user.id
    )
    res = await db.execute(stmt)
    exp = res.scalars().first()
    if not exp:
        raise ResourceNotFoundException("Work experience entry not found.")

    exp.company = body.company
    exp.title = body.title
    exp.location = body.location
    exp.start_date = body.start_date
    exp.end_date = None if body.is_current else body.end_date
    exp.is_current = body.is_current
    exp.description = body.description

    await db.commit()
    await db.refresh(exp)
    return ExperienceDTO.model_validate(exp)


@router.delete("/users/me/experiences/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experience(
    experience_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-011: Delete a work experience entry."""
    stmt = select(Experience).where(
        Experience.id == experience_id,
        Experience.user_id == current_user.id
    )
    res = await db.execute(stmt)
    exp = res.scalars().first()
    if not exp:
        raise ResourceNotFoundException("Work experience entry not found.")

    await db.delete(exp)
    await db.commit()
    return None


# ==============================================================================
# EDUCATIONS
# ==============================================================================

@router.post("/users/me/educations", response_model=EducationDTO, status_code=status.HTTP_201_CREATED)
async def add_education(
    body: EducationCreateDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-012: Add an academic education entry to authenticated user's profile."""
    edu_id = f"edu_{uuid.uuid4().hex[:12]}"
    edu = Education(
        id=edu_id,
        user_id=current_user.id,
        institution=body.institution,
        degree=body.degree,
        field_of_study=body.field_of_study,
        start_year=body.start_year,
        end_year=body.end_year,
    )
    db.add(edu)
    await db.commit()
    await db.refresh(edu)
    return EducationDTO.model_validate(edu)


@router.put("/users/me/educations/{education_id}", response_model=EducationDTO, status_code=status.HTTP_200_OK)
async def update_education(
    education_id: str,
    body: EducationUpdateDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-013: Update an existing education entry."""
    stmt = select(Education).where(
        Education.id == education_id,
        Education.user_id == current_user.id
    )
    res = await db.execute(stmt)
    edu = res.scalars().first()
    if not edu:
        raise ResourceNotFoundException("Education entry not found.")

    edu.institution = body.institution
    edu.degree = body.degree
    edu.field_of_study = body.field_of_study
    edu.start_year = body.start_year
    edu.end_year = body.end_year

    await db.commit()
    await db.refresh(edu)
    return EducationDTO.model_validate(edu)


@router.delete("/users/me/educations/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_education(
    education_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-014: Delete an education entry."""
    stmt = select(Education).where(
        Education.id == education_id,
        Education.user_id == current_user.id
    )
    res = await db.execute(stmt)
    edu = res.scalars().first()
    if not edu:
        raise ResourceNotFoundException("Education entry not found.")

    await db.delete(edu)
    await db.commit()
    return None


# ==============================================================================
# SKILLS
# ==============================================================================

@router.get("/skills", response_model=List[SkillDTO], status_code=status.HTTP_200_OK)
async def search_skills(
    query: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-015: Autocomplete & search canonical skills catalog."""
    stmt = select(Skill)
    if query:
        stmt = stmt.where(Skill.name.ilike(f"%{query.strip()}%"))
    stmt = stmt.order_by(Skill.name.asc()).limit(50)
    res = await db.execute(stmt)
    return [SkillDTO.model_validate(s) for s in res.scalars().all()]


@router.post("/users/me/skills", response_model=SkillDTO, status_code=status.HTTP_201_CREATED)
async def add_user_skill(
    body: UserSkillAddDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-016: Associate a canonical skill with authenticated user profile."""
    skill_name = body.skill_name.strip()
    # Find existing canonical skill or create new
    stmt = select(Skill).where(func.lower(Skill.name) == skill_name.lower())
    res = await db.execute(stmt)
    skill = res.scalars().first()

    if not skill:
        skill = Skill(
            id=f"skl_{uuid.uuid4().hex[:10]}",
            name=skill_name,
            category="Other",
        )
        db.add(skill)
        await db.flush()

    # Check if user already has skill
    us_stmt = select(UserSkill).where(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id == skill.id
    )
    us_res = await db.execute(us_stmt)
    existing_us = us_res.scalars().first()
    if not existing_us:
        us = UserSkill(
            id=f"us_{current_user.id}_{skill.id}",
            user_id=current_user.id,
            skill_id=skill.id,
        )
        db.add(us)
        await db.commit()

    return SkillDTO.model_validate(skill)


@router.delete("/users/me/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_skill(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-017: Disassociate a skill tag from authenticated user profile."""
    stmt = select(UserSkill).where(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id == skill_id
    )
    res = await db.execute(stmt)
    us = res.scalars().first()
    if us:
        await db.delete(us)
        await db.commit()
    return None
