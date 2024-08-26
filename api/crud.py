from sqlalchemy.orm import Session
from . import database

def get_user_by_email(db: Session, email: str):
    return db.query(database.User).filter(database.User.email == email).first()

def create_user(db: Session, email: str, senha: str):
    db_user = database.User(email=email, senha=senha)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
