from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import Timestamps, UUIDPrimaryKey


class Source(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "sources"
    is_example: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    __table_args__ = (
        CheckConstraint("url ~ '^https?://[^[:space:]]+$'", name="http_url"),
        CheckConstraint(
            "source_type IN ('OFFICIAL','LEGISLATION','SCIENTIFIC_STUDY','TECHNICAL_REPORT',"
            "'INSTITUTIONAL_REPORT','JOURNALISM','OTHER')",
            name="source_type",
        ),
    )

    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(300))
    institution: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(30))
    publication_date: Mapped[date | None]
    accessed_at: Mapped[date]
    description: Mapped[str | None] = mapped_column(Text)
