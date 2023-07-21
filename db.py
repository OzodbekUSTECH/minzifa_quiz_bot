from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import String, Column, Integer, Boolean, ForeignKey, Text, BigInteger
DATABASE_URL = "postgresql://postgres:77girado@localhost:5432/quez"


engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = Session()
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(BigInteger, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)





class GroupQuestion(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    questions = relationship("Question", back_populates='group')


class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True, index=True)
    question_number = Column(Integer)  # Add a new column for the question number
    question = Column(String)
    answer = Column(Text)

    group_id = Column(Integer, ForeignKey("groups.id"))
    group = relationship("GroupQuestion", back_populates="questions")
