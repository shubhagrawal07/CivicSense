from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.errors import InvalidInput
from app.models import Report, User
from app.models.enums import UserRole
from app.schemas.report import ReportAccepted, ReportOut
from app.services.reports import (
    build_report_out,
    check_region,
    clean_description,
    create_report,
)
from app.services.uploads import delete_image, save_image
from app.workers.pipeline import process_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("", response_model=ReportAccepted, status_code=202)
async def submit_report(
    background: BackgroundTasks,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    latitude: Annotated[float, Form(ge=-90, le=90)],
    longitude: Annotated[float, Form(ge=-180, le=180)],
    description: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
):
    text = clean_description(description)
    # browsers send an empty part when no file was picked
    has_image = image is not None and bool(image.filename)
    if text is None and not has_image:
        raise InvalidInput("description", "Provide a description, an image, or both")
    check_region(latitude, longitude)

    image_name = await save_image(image) if has_image else None
    try:
        report = create_report(db, user.id, text, image_name, latitude, longitude)
    except Exception:
        if image_name:
            delete_image(image_name)
        raise

    background.add_task(process_report, report.id)
    return report


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    # the ticket asks for 403 here, even though it lets callers probe which ids exist
    if user.role != UserRole.ADMIN and report.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return build_report_out(db, report)
