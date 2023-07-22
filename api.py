from fastapi import FastAPI, HTTPException, Body, status, Query
from db import *
import schema
app = FastAPI()


@app.put('/user/{user_id}')
async def update_user(user_id: int, first_name: str = None, last_name: str = None, is_superuser: bool = False):
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if first_name is not None:
        db_user.first_name = first_name
    if last_name is not None:
        db_user.last_name = last_name
    if is_superuser is not False:
        db_user.is_superuser = is_superuser
    db.commit()

    return {"message":"Данные были изменены!"}



@app.post('/add/username')
async def add_username(phone_number: str = None, is_superuser: bool = False):
    
    db_user_phone = db.query(User).filter(User.phone_number == phone_number).first()
    if db_user_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already exists")

    new_user = User(phone_number=phone_number, is_superuser = is_superuser)
    db.add(new_user)
    db.commit()

    return {"message": "User added successfully"}


@app.get('/users')
async def get_users():
    users = db.query(User).all()
    response = []
    for user in users:
        data = {
            "id": user.id,
            "tg_id": user.tg_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "is_superuser": user.is_superuser
        }

        response.append(data)
    
    return response


@app.delete('/user/{user_id}')
async def delete_user(user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    db.delete(db_user)
    db.commit()

    return {"message": "User deleted"}






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

@app.delete('/group/{group_id}', response_model=schema.GroupSchema)
async def delete_group(group_id: int, name: str):
        db_group = db.query(GroupQuestion).filter(GroupQuestion.id == group_id).first()
        for question in db_group.questions:
            db.delete(question)
        db.delete(db_group)
        db.commit()

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect group_id or something went wrong")
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

    # Delete the question from the database
    db.delete(db_question)
    db.commit()

    # Get the remaining questions within the same group, sorted by question_number
    remaining_questions = db.query(Question).filter(Question.group_id == group_id).order_by(Question.question_number).all()

    # Renumber the remaining questions within the group starting from 1
    for index, question in enumerate(remaining_questions, 1):
        question.question_number = index

    db.commit()

    return db_question