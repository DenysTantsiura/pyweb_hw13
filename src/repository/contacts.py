# функції для взаємодії з базою даних.
from datetime import date, timedelta
from typing import Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import cast, func, or_, String
from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemes import ContactModel, CatToNameModel, ContactResponse


async def get_contacts(
                       user: User, 
                       db: Session
                       ) -> Page[ContactResponse]:
    """To retrieve a list of records from a database with the ability to skip 
    a certain number of records and limit the number returned."""
    return paginate(
                    db.query(Contact)
                    .filter(Contact.user_id == user.id)
                    .order_by(Contact.name)
                    )


async def get_contact(
                      contact_id: int, 
                      user: User,
                      db: Session
                      ) -> Optional[Contact]:
    """To get a particular record by its ID."""
    return (
            db.query(Contact)
            .filter(Contact.user_id == user.id)
            .filter_by(id=contact_id)
            .first()
            )


async def create_contact(
                         body: ContactModel, 
                         user: User,
                         db: Session
                         ) -> Contact:
    """Creating a new record in the database. Takes a ContactModel object and uses the information 
    from it to create a new Contact object, then adds it to the session and 
    commits the changes to the database."""
    contact = (db.query(Contact).filter(Contact.user_id == user.id).filter_by(email=body.email).first() or
               db.query(Contact).filter(Contact.user_id == user.id).filter_by(phone=body.phone).first() or
               db.query(Contact).filter(Contact.user_id == user.id).filter_by(name=body.name, 
                                                                              last_name=body.last_name).first())
    if contact:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Duplicate data')
    
    contact = Contact(**body.dict(), user_id=user.id)  # , user_id=user.id  or , user=user
    db.add(contact)
    db.commit()
    db.refresh(contact)

    return contact


async def update_contact(
                         contact_id: int,
                         body: ContactModel,
                         user: User,
                         db: Session
                         ) -> Contact:
    """Update a specific record by its ID. Takes the ContactModel object and updates the information from it 
    by the name of the record. If the record does not exist - None is returned."""
    contact: Contact = db.query(Contact).filter(Contact.user_id == user.id).filter_by(id=contact_id).first()
    # contact: Contact = db.query(Contact).filter(Contact.user_id == user.id).filter(Contact.id == contact_id).first()
    
    db_obj_data = jsonable_encoder(contact)
    body_data = jsonable_encoder(body)
    
    for field in db_obj_data:
        if field in body_data:
            setattr(contact, field, body_data[field])
            
    db.add(contact)
    db.commit()
    db.refresh(contact)

    return contact


async def remove_contact(
                         contact_id: int,
                         user: User,
                         db: Session
                         ) -> Optional[Contact]:
    """Delete a specific record by its ID. If the record does not exist - None is returned."""
    contact = db.query(Contact).filter(Contact.user_id == user.id).filter_by(id=contact_id).first()
    if contact:
        db.delete(contact)
        db.commit()

    return contact


async def change_name_contact(
                              body: CatToNameModel,
                              contact_id: int,
                              user: User,
                              db: Session
                              ) -> Optional[Contact]:
    """To update only the name of the record."""
    contact = db.query(Contact).filter(Contact.user_id == user.id).filter_by(id=contact_id).first()
    if contact:
        contact.name = body.name
        db.commit()

    return contact


# -=- AND--------------------------------------------------------------
async def search_by_fields_and(
                            #    body: ContactQuery,
                               name: str | None,
                               last_name: str | None,
                               email: str | None,
                               phone: int | None,
                               user: User,
                               db: Session
                               ) -> Optional[Contact]:
    """To search for a record by a specific value for field(-s)."""
    # body_data = jsonable_encoder(body)
    # if not any(body_data.values()):

    #     return None
    
    # result = db.query(Contact).filter(Contact.user_id == user.id)
    # for field in body_data:
    #     if body[field]:
    #         result = result.filter_by(field=body[field])

    if not name and not last_name and not email and not phone:
        return None

    result = db.query(Contact).filter(Contact.user_id == user.id)
    if name:
        result = result.filter_by(name=name)
    if last_name:
        result = result.filter_by(last_name=last_name)
    if email:
        result = result.filter_by(email=email)
    if phone:
        result = result.filter_by(phone=phone)

    return result.first()  # db.query(Contact).filter(Contact.user_id == user.id).filter_by(name=name).first()


# -=- OR ----------------------------------------------------------------
async def search_by_fields_or(
                              query_str: str,
                              user: User,
                              db: Session
                              ) -> Page[ContactResponse]:
    """To search for an entry by match in all fields: name, last_name, query, phone."""
    return paginate(
                    db.query(Contact)
                    .filter(Contact.user_id == user.id)
                    .filter(
                            or_(
                                Contact.name == query_str, 
                                Contact.last_name == query_str,
                                Contact.email == query_str,
                                cast(Contact.phone, String) == query_str   # !?,
                                )
                            )
                    )


# https://stackoverflow.com/questions/7942547/using-or-in-sqlalchemy
# -like- OR------------------------------------------------------------
async def search_by_like_fields_or(
                                   query_str: str,
                                   user: User,
                                   db: Session
                                   ) -> Page[ContactResponse]:
    """To search for an entry by a partial match in all fields: name, last_name, query, phone."""
    return paginate(
                    db.query(Contact)
                    .filter(Contact.user_id == user.id)
                    .filter(
                            or_(
                                Contact.name.icontains(query_str), 
                                Contact.last_name.icontains(query_str),
                                Contact.email.icontains(query_str),
                                cast(Contact.phone, String).icontains(str(query_str))
                                )
                            )
                    )


# -like- AND-------------------------------------------------------
async def search_by_like_fields_and(
                                    part_name: str | None,
                                    part_last_name: str | None,
                                    part_email: str | None,
                                    part_phone: int | None,
                                    user: User,
                                    db: Session
                                    ) -> Page[ContactResponse]:
    """To search for an entry by a partial match in all fields: name, last_name, query, phone."""
    if not part_name and not part_last_name and not part_email and not part_phone:
        return None

    result = db.query(Contact).filter(Contact.user_id == user.id)
    if part_name:
        result = result.filter(Contact.name.icontains(part_name))
    if part_last_name:
        result = result.filter(Contact.last_name.icontains(part_last_name))
    if part_email:
        result = result.filter(Contact.email.icontains(part_email))
    if part_phone:
        result = result.filter(cast(Contact.phone, String).icontains(str(part_phone)))
    
    return paginate(result)


# ------- search_by_birthday... --------------------------------------------
async def search_by_birthday_celebration_within_days(
                                                     meantime: int,   
                                                     user: User,
                                                     db: Session
                                                     ) -> Page[ContactResponse]: 
    """To find contacts celebrating birthdays in the next (meantime) days."""
    today = date.today()
    days_limit = date.today() + timedelta(meantime)
    slide = 1 if days_limit.year - today.year else 0

    return paginate(
                    db.query(Contact)
                    .filter(Contact.user_id == user.id)
                    .filter(func.to_char(Contact.birthday, f'{slide}MM-DD') >= today.strftime(f"0%m-%d"),
                            func.to_char(Contact.birthday, '0MM-DD') <= days_limit.strftime(f"{slide}%m-%d"))
                    )
