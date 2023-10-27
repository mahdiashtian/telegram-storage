from typing import Optional, List, Type

from sqlalchemy.orm import Session

from models import User, File


def read_users(db: Session) -> List[Type[User]]:
    query = db.query(User)

    db_users = query.all()
    db_users.sort(key=lambda x: x.id)

    return db_users


def read_user_from_db(db: Session, user_id: int) -> Optional[Type[User]]:
    return db.query(User).filter(User.userid == user_id).first()


def create_user_from_db(db: Session, data: dict) -> User:
    db_user = User(**data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def create_file_from_db(db: Session, data: dict) -> File:
    db_file = File(**data)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return db_file


def delete_file_from_db(db: Session, userid: object, code: int) -> None:
    db.query(File).filter(File.code == code, File.owner_id == userid).delete()
    db.commit()


def read_files_from_db(db: Session, code: int = None, userid: int = None) -> List[Type[File]]:
    obj = db.query(File)
    if code is not None:
        obj = obj.filter(File.code == code)
    if userid is not None:
        obj = obj.filter(File.owner_id == userid)
    return obj.all()


def read_file_from_db(db: Session, code: int = None, userid: int = None) -> Optional[Type[File]]:
    obj = read_files_from_db(db, code, userid)
    return obj[0] if obj else None
