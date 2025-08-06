from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ParsedCV(Base):
    __tablename__ = "parsed_cvs"
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    skills = Column(Text)
    text_preview = Column(Text)
    location = Column(String)     # candidate location
    degrees = Column(Text)        # semicolon-separated degrees
    universities = Column(Text)   # semicolon-separated universities
    #comment
