"""Job board and Mini-ATS applicant tracking pipeline API router (API-034 through API-041)."""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import (
    JobNotFoundException,
    NotJobOwnerException,
    AlreadyAppliedToJobException,
    ResourceNotFoundException,
)
from app.api.deps import get_current_user
from app.models.schema import Job, JobApplication, User, Profile, UserSkill, Skill, Notification
from app.schemas.contracts import (
    JobDTO,
    CreateJobDTO,
    UpdateJobStatusDTO,
    EasyApplyDTO,
    JobApplicationDTO,
    UpdateApplicationStatusDTO,
    UserSummaryDTO,
    WorkplaceType,
    JobStatus,
    ApplicationStatus,
    CursorPaginatedResponse,
)
from app.api.ws.manager import manager

logger = logging.getLogger("pronet.jobs")
router = APIRouter(prefix="/jobs", tags=["Job Board & Mini-ATS Pipeline"])


def format_user_summary(user: User) -> UserSummaryDTO:
    """Build UserSummaryDTO from User and Profile."""
    p = user.profile
    return UserSummaryDTO(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        headline=p.headline if p else "",
        avatar_url=p.avatar_url if p else None,
    )


def format_job_dto(
    job: Job,
    has_viewer_applied: bool = False,
    viewer_status: Optional[ApplicationStatus] = None
) -> JobDTO:
    """Serialize Job entity into JobDTO with required skills parsed from JSON."""
    skills = []
    try:
        skills = json.loads(job.required_skills) if job.required_skills else []
    except Exception:
        skills = []

    return JobDTO(
        id=job.id,
        poster=format_user_summary(job.poster),
        title=job.title,
        company_name=job.company_name,
        workplace_type=WorkplaceType(job.workplace_type),
        location=job.location,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        description=job.description,
        required_skills=skills,
        status=JobStatus(job.status),
        application_count=job.application_count,
        has_viewer_applied=has_viewer_applied,
        viewer_application_status=viewer_status,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def format_application_dto(app: JobApplication, job_title: Optional[str] = None, company: Optional[str] = None) -> JobApplicationDTO:
    """Serialize JobApplication entity into JobApplicationDTO."""
    skills = []
    try:
        skills = json.loads(app.skills_snapshot) if app.skills_snapshot else []
    except Exception:
        skills = []

    return JobApplicationDTO(
        id=app.id,
        job_id=app.job_id,
        job_title=job_title or (app.job.title if app.job else None),
        company_name=company or (app.job.company_name if app.job else None),
        applicant=format_user_summary(app.applicant),
        status=ApplicationStatus(app.status),
        cover_note=app.cover_note,
        resume_url=app.resume_url,
        profile_headline_snapshot=app.profile_headline_snapshot,
        skills_snapshot=skills,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


# ==============================================================================
# JOB SEARCH & DETAIL
# ==============================================================================

@router.get("", response_model=CursorPaginatedResponse[JobDTO], status_code=status.HTTP_200_OK)
async def search_jobs(
    keyword: Optional[str] = Query(None),
    workplace_type: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    job_status: Optional[str] = Query("OPEN", alias="status"),
    limit: int = Query(20, ge=1, le=50),
    cursor: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-034: Search and filter jobs with facet filters and cursor pagination."""
    stmt = (
        select(Job)
        .options(selectinload(Job.poster).selectinload(User.profile))
    )

    if job_status and job_status.upper() in ["OPEN", "CLOSED"]:
        stmt = stmt.where(Job.status == job_status.upper())

    if workplace_type and workplace_type.upper() in ["REMOTE", "HYBRID", "ON_SITE"]:
        stmt = stmt.where(Job.workplace_type == workplace_type.upper())

    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location.strip()}%"))

    if keyword:
        kw = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                Job.title.ilike(kw),
                Job.company_name.ilike(kw),
                Job.description.ilike(kw),
            )
        )

    if skill:
        sk = f"%{skill.strip()}%"
        stmt = stmt.where(Job.required_skills.ilike(sk))

    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            stmt = stmt.where(Job.created_at < cursor_dt)
        except Exception as exc:
            logger.debug("Failed parsing cursor datetime for jobs query: %s (%s)", cursor, exc)

    fetch_limit = min(limit, 50) + 1
    stmt = stmt.order_by(Job.created_at.desc()).limit(fetch_limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()

    has_more = len(rows) > min(limit, 50)
    target_jobs = rows[:min(limit, 50)]

    job_ids = [j.id for j in target_jobs]
    # Check viewer applications for these jobs
    apps_stmt = select(JobApplication).where(
        JobApplication.job_id.in_(job_ids),
        JobApplication.applicant_id == current_user.id
    )
    apps_res = await db.execute(apps_stmt)
    user_apps = {a.job_id: ApplicationStatus(a.status) for a in apps_res.scalars().all()}

    items = [
        format_job_dto(
            j,
            has_viewer_applied=(j.id in user_apps),
            viewer_status=user_apps.get(j.id)
        )
        for j in target_jobs
    ]

    next_cursor = None
    if has_more and target_jobs:
        c_val = target_jobs[-1].created_at
        if hasattr(c_val, "isoformat"):
            next_cursor = c_val.isoformat().replace("+00:00", "Z")

    return CursorPaginatedResponse[JobDTO](
        items=items,
        next_cursor=next_cursor,
        has_more=has_more
    )


@router.get("/applications/me", response_model=List[JobApplicationDTO], status_code=status.HTTP_200_OK)
async def list_my_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-041: List job applications submitted by the authenticated user."""
    stmt = (
        select(JobApplication)
        .options(
            selectinload(JobApplication.job),
            selectinload(JobApplication.applicant).selectinload(User.profile),
        )
        .where(JobApplication.applicant_id == current_user.id)
        .order_by(JobApplication.created_at.desc())
    )
    res = await db.execute(stmt)
    apps = res.scalars().all()
    return [format_application_dto(a) for a in apps]


@router.get("/{job_id}", response_model=JobDTO, status_code=status.HTTP_200_OK)
async def get_job_detail(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-035: Retrieve single job listing detail."""
    stmt = (
        select(Job)
        .options(selectinload(Job.poster).selectinload(User.profile))
        .where(Job.id == job_id)
    )
    res = await db.execute(stmt)
    job = res.scalars().first()
    if not job:
        raise JobNotFoundException()

    app_stmt = select(JobApplication).where(
        JobApplication.job_id == job_id,
        JobApplication.applicant_id == current_user.id
    )
    app_res = await db.execute(app_stmt)
    user_app = app_res.scalars().first()

    return format_job_dto(
        job,
        has_viewer_applied=(user_app is not None),
        viewer_status=ApplicationStatus(user_app.status) if user_app else None
    )


@router.post("", response_model=JobDTO, status_code=status.HTTP_201_CREATED)
async def create_job(
    body: CreateJobDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-036: Post new job listing (recruiter / hiring manager)."""
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job = Job(
        id=job_id,
        poster_id=current_user.id,
        title=body.title.strip(),
        company_name=body.company_name.strip(),
        workplace_type=body.workplace_type.value,
        location=body.location.strip(),
        salary_min=body.salary_min,
        salary_max=body.salary_max,
        description=body.description.strip(),
        required_skills=json.dumps(body.required_skills),
        status="OPEN",
        application_count=0,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Re-fetch with poster loaded
    stmt = (
        select(Job)
        .options(selectinload(Job.poster).selectinload(User.profile))
        .where(Job.id == job.id)
    )
    res = await db.execute(stmt)
    hydrated_job = res.scalars().first()
    return format_job_dto(hydrated_job, has_viewer_applied=False, viewer_status=None)


@router.patch("/{job_id}/status", response_model=JobDTO, status_code=status.HTTP_200_OK)
async def toggle_job_status(
    job_id: str,
    body: UpdateJobStatusDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-037: Toggle job status (OPEN / CLOSED). Owner only."""
    stmt = (
        select(Job)
        .options(selectinload(Job.poster).selectinload(User.profile))
        .where(Job.id == job_id)
    )
    res = await db.execute(stmt)
    job = res.scalars().first()
    if not job:
        raise JobNotFoundException()

    if job.poster_id != current_user.id:
        raise NotJobOwnerException("Only the job poster can change the job status.")

    job.status = body.status.value
    await db.commit()
    await db.refresh(job)
    return format_job_dto(job)


@router.post("/{job_id}/apply", response_model=JobApplicationDTO, status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    job_id: str,
    body: EasyApplyDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-038: Easy Apply application submission with candidate profile snapshot."""
    stmt = (
        select(Job)
        .options(selectinload(Job.poster).selectinload(User.profile))
        .where(Job.id == job_id)
    )
    res = await db.execute(stmt)
    job = res.scalars().first()
    if not job:
        raise JobNotFoundException()

    # Prevent duplicate applications (EDG-003)
    existing_stmt = select(JobApplication).where(
        JobApplication.job_id == job_id,
        JobApplication.applicant_id == current_user.id
    )
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalars().first():
        raise AlreadyAppliedToJobException()

    # Snapshot current headline & skills
    profile_headline = current_user.profile.headline if current_user.profile else "Professional"

    skills_stmt = (
        select(Skill.name)
        .join(UserSkill, UserSkill.skill_id == Skill.id)
        .where(UserSkill.user_id == current_user.id)
    )
    skills_res = await db.execute(skills_stmt)
    skills_list = list(skills_res.scalars().all())

    app_id = f"app_{uuid.uuid4().hex[:12]}"
    app = JobApplication(
        id=app_id,
        job_id=job_id,
        applicant_id=current_user.id,
        status="APPLIED",
        cover_note=body.cover_note,
        resume_url=body.resume_url,
        profile_headline_snapshot=profile_headline,
        skills_snapshot=json.dumps(skills_list),
    )
    db.add(app)

    # Increment job application counter
    job.application_count += 1

    # Notify recruiter
    if job.poster_id != current_user.id:
        notif = Notification(
            id=f"notif_{uuid.uuid4().hex[:12]}",
            user_id=job.poster_id,
            actor_id=current_user.id,
            notification_type="JOB_STATUS_CHANGE",
            title="New Job Applicant",
            content=f"{current_user.full_name} applied to your job listing '{job.title}'.",
            reference_id=job.id,
            reference_type="JOB",
            is_read=False,
        )
        db.add(notif)

    await db.commit()
    await db.refresh(app)

    if job.poster_id != current_user.id:
        await manager.push_badge_update(job.poster_id, db)

    return format_application_dto(app, job_title=job.title, company=job.company_name)


@router.get("/{job_id}/applications", response_model=List[JobApplicationDTO], status_code=status.HTTP_200_OK)
async def list_job_applications(
    job_id: str,
    application_status: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-039: View candidate pipeline for posted job (job owner only)."""
    job = await db.get(Job, job_id)
    if not job:
        raise JobNotFoundException()

    if job.poster_id != current_user.id:
        raise NotJobOwnerException()

    stmt = (
        select(JobApplication)
        .options(
            selectinload(JobApplication.job),
            selectinload(JobApplication.applicant).selectinload(User.profile),
        )
        .where(JobApplication.job_id == job_id)
    )
    if application_status and application_status.upper() in ["APPLIED", "REVIEWING", "SHORTLISTED", "REJECTED"]:
        stmt = stmt.where(JobApplication.status == application_status.upper())

    stmt = stmt.order_by(JobApplication.created_at.desc())
    res = await db.execute(stmt)
    return [format_application_dto(a) for a in res.scalars().all()]


@router.patch("/{job_id}/applications/{application_id}/status", response_model=JobApplicationDTO, status_code=status.HTTP_200_OK)
async def update_applicant_status(
    job_id: str,
    application_id: str,
    body: UpdateApplicationStatusDTO,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """API-040: Update candidate status in recruitment pipeline (owner only)."""
    job = await db.get(Job, job_id)
    if not job:
        raise JobNotFoundException()

    if job.poster_id != current_user.id:
        raise NotJobOwnerException()

    stmt = (
        select(JobApplication)
        .options(
            selectinload(JobApplication.job),
            selectinload(JobApplication.applicant).selectinload(User.profile),
        )
        .where(JobApplication.id == application_id, JobApplication.job_id == job_id)
    )
    res = await db.execute(stmt)
    app = res.scalars().first()
    if not app:
        raise ResourceNotFoundException("Application record not found.")

    app.status = body.status.value

    # Notify applicant about status change
    notif = Notification(
        id=f"notif_{uuid.uuid4().hex[:12]}",
        user_id=app.applicant_id,
        actor_id=current_user.id,
        notification_type="JOB_STATUS_CHANGE",
        title="Application Status Updated",
        content=f"Your application status for '{job.title}' was updated to {body.status.value}.",
        reference_id=job.id,
        reference_type="JOB",
        is_read=False,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(app)

    await manager.push_badge_update(app.applicant_id, db)
    return format_application_dto(app)
