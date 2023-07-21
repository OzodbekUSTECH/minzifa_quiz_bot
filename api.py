from fastapi import FastAPI, HTTPException, Body, status, Query
from db import *
import schema
app = FastAPI()



@app.get('/groups', response_model=list[schema.GroupSchema])
async def get_groups():
    all_groups = db.query(GroupQuestion).order_by('id').all()
    response = []
    for group in all_groups:
        last_question = db.query(Question).filter(Question.group_id == group.id).order_by(Question.question_number.desc()).first()
        last_question_number = last_question.question_number if last_question else 0

        group_data = schema.GroupSchema(
            id = group.id,
            name = group.name,
            amount_questions=last_question_number
        )
        response.append(group_data)

    return response

@app.get("/group/{group_id}", response_model=schema.GroupSchema)
async def get_group_by_id(group_id: int):
    db_group = db.query(GroupQuestion).filter(GroupQuestion.id == group_id).first()

    last_question = db.query(Question).filter(Question.group_id == db_group.id).order_by(Question.question_number.desc()).first()
    last_question_number = last_question.question_number if last_question else 0

    response = schema.GroupSchema(
        id = db_group.id,
        name = db_group.name,
        amount_questions= last_question_number
    )

    return response

@app.post('/group', response_model=schema.GroupSchema)
async def group_create(name: str):
    new_group = GroupQuestion(name=name)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    
    return new_group

@app.put('/group/{group_id}', response_model=schema.GroupSchema)
async def group_update(group_id: int, name: str):
        db_group = db.query(GroupQuestion).filter(GroupQuestion.id == group_id).first()

        if name is not None:
             db_group.name = name
            
        db.commit()
        db.refresh(db_group)

        return db_group


###############################################################################################################################
###############################################################################################################################


@app.get("/group/{group_id}/questions", response_model = list[schema.QuestionSchema])
async def get_all_questions_of_group(group_id: int, page: int = Query(1, ge=1), per_page: int = Query(100, le=100)):
    # Calculate the offset to skip questions based on the requested page and per_page values
    offset = (page - 1) * per_page

    # Query the questions with pagination
    all_questions = db.query(Question).filter(Question.group_id == group_id).order_by('question_number').offset(offset).limit(per_page).all()

    return all_questions



###############################################################################################################################
###############################################################################################################################
###############################################################################################################################
from typing import List

@app.get('/questions', response_model=List[schema.QuestionSchema])
async def get_all_questions(page: int = Query(1, ge=1), per_page: int = Query(100, le=100)):
    # Calculate the offset to skip questions based on the requested page and per_page values
    offset = (page - 1) * per_page

    # Query the questions with pagination
    all_questions = db.query(Question).order_by('id').offset(offset).limit(per_page).all()

    return all_questions


@app.get('/question/{question_id}', response_model=schema.QuestionSchema)
async def get_question_by_id(question_id: int):
    question = db.query(Question).filter(Question.id == question_id).first()

    return question



@app.post('/question', response_model=schema.QuestionSchema)
async def create_question(new_question: schema.QuestionCreateSchema):
    # Query the last question for the given group
    last_question = db.query(Question).filter(Question.group_id == new_question.group_id).order_by(Question.question_number.desc()).first()
    next_question_number = 1 if last_question is None else last_question.question_number + 1

    # Create the new question with the determined question number
    new_question = Question(question_number=next_question_number, question=new_question.question, answer=new_question.answer, group_id=new_question.group_id)
    try:
        db.add(new_question)
        db.commit()
        db.refresh(new_question)  # Refresh the object to get its updated state from the database
    except:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect group_id or smth was wrong")
    return new_question


@app.put('/question/{question_id}', response_model=schema.QuestionSchema)
async def update_question_data(question_id: int, update_question: schema.QuestionUpdateSchema):
    db_question = db.query(Question).filter(Question.id == question_id).first()

    if update_question.group_id is not None:
          db_question.group_id = update_question.group_id
    if update_question.question is not None:
         db_question.question = update_question.question
    if update_question.answer is not None:
         db_question.answer = update_question.answer
    
    db.commit()
    db.refresh(db_question)

    return db_question

@app.delete('/question/{question_id}', response_model=schema.QuestionSchema)
async def delete_question(question_id: int):
    # Retrieve the question to be deleted
    db_question = db.query(Question).filter(Question.id == question_id).first()

    if not db_question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    group_id = db_question.group_id
    question_number = db_question.question_number
    db.delete(db_question)
    db.commit()

    # Get the remaining questions within the same group, sorted by question_number
    remaining_questions = db.query(Question).filter(Question.group_id == group_id).order_by(Question.question_number).all()

    # Renumber the remaining questions within the group
    for index, question in enumerate(remaining_questions, question_number):
        if question.question_number != index:
            question.question_number = index

    db.commit()

    return db_question