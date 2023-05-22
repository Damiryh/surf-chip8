from typing import List
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(500), nullable=False)

    snippets: Mapped[List["Snippet"]] = relationship(back_populates="author")
    
    def __init__(self, username, password):
        self.name = username
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def __repr__(self):
        return f"User #{self.id} {name}"

class Snippet(Base):
    __tablename__ = 'snippet'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String(5000), nullable=False)

    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    author: Mapped["User"] = relationship(back_populates="snippets")
    
    def __init__(self, author, name, source):
        self.name = name
        self.source = source
        self.author = author
    
    def __repr__(self):
        return f"Snippet #{self.id} '{self.name}' by {self.author.name}: '{self.source[:15]}...'"











