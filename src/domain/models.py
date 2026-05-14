from .db import Base, engine
from sqlalchemy import DateTime, String, Integer, Text, Numeric, Date, ForeignKey, Table, Column, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from typing import Optional

# 1. Taula auxiliar N:M (game_tag)
game_tag = Table(
    "game_tag",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("game.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tag.id"), primary_key=True),
)

class Platform(Base):
    __tablename__ = "platform"

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False
    )
    release_year: Mapped[Optional[int]] = mapped_column(Integer)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(50))
    generation: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Requisit Migració 2
    last_update: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now, 
        onupdate=datetime.now
    )

    games: Mapped[list["Game"]] = relationship(
        back_populates="platform"
    )

class UserAccount(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True
    )
    username: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        nullable=False
    )
    password: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    registration_date: Mapped[date] = mapped_column(
        Date, 
        default=date.today
    )

    # Requisit Migració 2
    last_update: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now, 
        onupdate=datetime.now
    )

    profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="user"
    )

class UserProfile(Base):
    __tablename__ = "user_profile"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user_account.id"),
        primary_key=True
    )
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    country: Mapped[Optional[str]] = mapped_column(String(50))
    city: Mapped[Optional[str]] = mapped_column(String(50))
    zip_code: Mapped[Optional[str]] = mapped_column(String(15))

    # Requisit Migració 2
    last_update: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now, 
        onupdate=datetime.now
    )

    user: Mapped["UserAccount"] = relationship(back_populates="profile")

class Game(Base):
    __tablename__ = "game"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    release_year: Mapped[Optional[int]] = mapped_column(Integer)

    platform_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("platform.id"),
        nullable=False
    )

    # Requisit Migració 2
    last_update: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now, 
        onupdate=datetime.now
    )

    platform: Mapped["Platform"] = relationship(back_populates="games")
    
    tags: Mapped[list["Tag"]] = relationship(
        secondary=game_tag,
        back_populates="games"
    )
    
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="game"
    )

class Tag(Base):
    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Requisit Migració 2
    last_update: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now, 
        onupdate=datetime.now
    )

    games: Mapped[list["Game"]] = relationship(
        secondary=game_tag,
        back_populates="tags"
    )

class Review(Base):
    __tablename__ = "review"

    game_id: Mapped[int] = mapped_column(
        ForeignKey("game.id"), 
        primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.id"), 
        primary_key=True
    )

    score: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    review_date: Mapped[date] = mapped_column(Date, default=date.today)

    # Requisit Migració 2
    last_update: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now, 
        onupdate=datetime.now
    )

    game: Mapped["Game"] = relationship(back_populates="reviews")
    user: Mapped["UserAccount"] = relationship(back_populates="reviews")

    __table_args__ = (
        CheckConstraint('score >= 1 AND score <= 10', name='check_score_range'),
    )