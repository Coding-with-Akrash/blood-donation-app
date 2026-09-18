"""Initial blood donation department schema."""
from alembic import op
from app.database import Base
import app.models  # noqa: F401

revision = "20260917_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Metadata is deliberately imported from the versioned application release.
    # Future changes must be introduced as new Alembic revisions, never by create_all.
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)
