from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import AdminUser, require_admin

from ..models import Agent, Finding

from ..schemas import FindingResponse


router = APIRouter(
    prefix="/findings",
    tags=["Findings"],
)


@router.get(
    "",
    response_model=list[FindingResponse],
)
def get_findings(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
):

    return (
        db.query(Finding)
        .order_by(
            Finding.created_at.desc()
        )
        .all()
    )
