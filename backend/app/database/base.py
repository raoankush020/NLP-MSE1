from app.database.session import Base
# Import all models here so Alembic or Base.metadata.create_all has access to them
from app.models.models import (
    User,
    Document,
    DocumentChunk,
    QueryRecord,
    RetrievedChunk,
    Evaluation,
    Claim,
    UserSetting
)
