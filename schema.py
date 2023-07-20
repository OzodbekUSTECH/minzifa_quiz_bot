from pydantic import BaseModel

class GroupSchema(BaseModel):
    id: int
    name: str
    amount_questions: int = 0

    class Config:
        orm_mode = True



class QuestionSchema(BaseModel):
    id: int
    question_number: int
    question: str
    answer: str
    group_id: int

    class Config:
        orm_mode = True


class QuestionCreateSchema(BaseModel):
    question: str
    answer: str
    group_id: int

class QuestionUpdateSchema(BaseModel):
    question: str
    answer: str
    group_id: int