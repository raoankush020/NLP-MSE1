from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import User, UserSetting
from app.schemas.schemas import UserSettingsDTO, UpdateSettingsRequest
from app.api.deps import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=UserSettingsDTO)
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    setting = db.query(UserSetting).filter(UserSetting.user_id == current_user.id).first()
    if not setting:
        setting = UserSetting(user_id=current_user.id)
        db.add(setting)
        db.commit()
        db.refresh(setting)

    return UserSettingsDTO(
        llm_model=setting.llm_model,
        temperature=setting.temperature,
        top_k=setting.top_k,
        chunk_size=setting.chunk_size,
        chunk_overlap=setting.chunk_overlap,
        embedding_model=setting.embedding_model,
        has_custom_api_key=bool(setting.custom_api_key)
    )

@router.put("", response_model=UserSettingsDTO)
def update_settings(
    request: UpdateSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    setting = db.query(UserSetting).filter(UserSetting.user_id == current_user.id).first()
    if not setting:
        setting = UserSetting(user_id=current_user.id)
        db.add(setting)

    if request.llm_model is not None:
        setting.llm_model = request.llm_model
    if request.temperature is not None:
        setting.temperature = request.temperature
    if request.top_k is not None:
        setting.top_k = request.top_k
    if request.chunk_size is not None:
        setting.chunk_size = request.chunk_size
    if request.chunk_overlap is not None:
        setting.chunk_overlap = request.chunk_overlap
    if request.embedding_model is not None:
        setting.embedding_model = request.embedding_model
    if request.custom_api_key is not None:
        setting.custom_api_key = request.custom_api_key.strip() if request.custom_api_key.strip() else None

    db.commit()
    db.refresh(setting)

    return UserSettingsDTO(
        llm_model=setting.llm_model,
        temperature=setting.temperature,
        top_k=setting.top_k,
        chunk_size=setting.chunk_size,
        chunk_overlap=setting.chunk_overlap,
        embedding_model=setting.embedding_model,
        has_custom_api_key=bool(setting.custom_api_key)
    )
