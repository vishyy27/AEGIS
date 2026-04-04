from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.settings import Settings
from ..schemas.core_schemas import SettingsResponse, SettingsBase

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    settings = db.query(Settings).first()
    if not settings:
        # Default settings if none exist
        settings = Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.put("/", response_model=SettingsResponse)
def update_settings(settings_in: SettingsBase, db: Session = Depends(get_db)):
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings(**settings_in.dict())
        db.add(settings)
    else:
        for key, value in settings_in.dict().items():
            setattr(settings, key, value)

    db.commit()
    db.refresh(settings)
    return settings
