from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)

    userid: Mapped[int] = mapped_column(BigInteger(), index=True, unique=True)
    phone_number: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(), default=datetime.utcnow)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_staff: Mapped[bool] = mapped_column(default=False)

    files: Mapped["File"] = relationship(back_populates="owner")


class Channel(Base):
    __tablename__ = "channel"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)

    channel_id: Mapped[str] = mapped_column(index=True)
    channel_link: Mapped[str] = mapped_column(index=True)


class File(Base):
    __tablename__ = "file"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True)

    type: Mapped[str] = mapped_column()
    size: Mapped[int] = mapped_column()
    code: Mapped[str] = mapped_column()
    file_id: Mapped[str] = mapped_column()
    count: Mapped[int] = mapped_column(default=0)
    password: Mapped[str] = mapped_column(nullable=True)
    caption: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(), default=datetime.utcnow)

    owner_id: Mapped[int] = mapped_column(BigInteger(), ForeignKey("user.userid"))
    owner: Mapped["User"] = relationship(back_populates="files")
