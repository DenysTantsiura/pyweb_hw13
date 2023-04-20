from datetime import date, timedelta
from typing import Optional

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi_pagination import Page, Params
# from fastapi_pagination import PaginationParams
from fastapi_pagination.bases import RawParams
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import cast, func, or_, String
from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemes import ContactModel, CatToNameModel, ContactResponse
from src.services.pagination import PageParams


async def get_contacts(
                       user: User, 
                       db: Session,
                       pagination_params: Params
                       ) -> Page:
    """
    The get_contacts function returns a paginated list of contacts for the user.

    :param user: User: Identify the user who is making the request
    :param db: Session: Access the database
    :return: Page: A page object
    :doc-author: Trelent
    """
    return paginate(
                    db.query(Contact)
                    .filter(Contact.user_id == user.id)
                    .order_by(Contact.name),
                    pagination_params
                    )


async def get_contact(
                      contact_id: int, 
                      user: User,
                      db: Session
                      ) -> Optional[Contact]:
    """
    The get_contact function returns a contact from the database.

    :param contact_id: int: Specify the id of the contact to be returned
    :param user: User: Get the user_id from the user object
    :param db: Session: Pass the database session to the function
    :return: A single contact
    :doc-author: Trelent
    """
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
    """
    The create_contact function creates a new contact in the database.
        Args:
            body (ContactModel): The contact to create.
            user (User): The current user, who is creating the contact.

    :param body: ContactModel: Validate the data sent by the user
    :param user: User: Get the user id from the token
    :param db: Session: Access the database
    :return: A contact object
    :doc-author: Trelent
    """
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
                         ) -> Optional[Contact]:
    """
    Update a specific record by its ID. Takes the ContactModel object and updates the information from it
    by the name of the record. If the record does not exist - None is returned.

    :param contact_id: int: Contact ID
    :param body: ContactModel: Validate the data sent by the user
    :param user: User: Get the user id from the token
    :param db: Session: Access the database
    :return: A contact object
    """
    contact: Contact = db.query(Contact).filter(Contact.user_id == user.id).filter_by(id=contact_id).first()
    # contact: Contact = db.query(Contact).filter(Contact.user_id == user.id).filter(Contact.id == contact_id).first()

    db_obj_data = contact.__dict__ if contact else None
    # db_obj_data = jsonable_encoder(contact) if contact else None
    
    body_data = jsonable_encoder(body) if body else None
    
    if not db_obj_data or not body_data:
        return None

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
    """
    The remove_contact function removes a contact from the database.
        Args:
            contact_id (int): The id of the contact to be removed.
            user (User): The user who is removing the contact. This is used to ensure that only contacts belonging
            to this user are removed.

    :param contact_id: int: Identify the contact to be removed
    :param user: User: Get the user_id from the database
    :param db: Session: Pass the database session to the function
    :return: The contact that was removed
    :doc-author: Trelent
    """
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
    """
    The change_name_contact function takes in a CatToNameModel, contact_id, user and db.
    It then queries the database for the contact with that id and changes its name to what is passed in.


    :param body: CatToNameModel: Get the name from the request body
    :param contact_id: int: Identify which contact to change the name of
    :param user: User: Get the user_id of the contact
    :param db: Session: Access the database
    :return: The contact object with the updated name
    :doc-author: Trelent
    """
    contact = db.query(Contact).filter(Contact.user_id == user.id).filter_by(id=contact_id).first()
    if contact:
        contact.name = body.name
        db.commit()

    return contact


# -=- AND--------------------------------------------------------------
async def search_by_fields_and(
                               name: str | None,
                               last_name: str | None,
                               email: str | None,
                               phone: int | None,
                               user: User,
                               db: Session
                               ) -> Optional[Contact]:
    """
    The search_by_fields_and function searches for a contact by name, last_name, email and phone.
        Args:
            name (str): The first name of the contact to search for.
            last_name (str): The last name of the contact to search for.
            email (str): The email address of the contact to search for.
            phone (int): The phone number of the contact to search for.

    :param name: str | None: Filter the results by name
    :param last_name: str | None: Filter by last name
    :param email: str | None: Search for a contact by email
    :param phone: int | None: Check if the phone number is an integer or none
    :param user: User: Check if the user is logged in
    :param db: Session: Access the database
    :return: The first result of the query
    :doc-author: Trelent
    """
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

    return result.first()


# -=- OR ----------------------------------------------------------------
async def search_by_fields_or(
                              query_str: str,
                              user: User,
                              db: Session
                              ) -> Page:
    """
    The search_by_fields_or function searches for contacts by name, last_name, email or phone.
        It returns a list of contacts that match the search criteria.

    :param query_str: str: Search for a contact by name, last_name, email or phone
    :param user: User: Filter the contacts by user
    :param db: Session: Pass the database session to the function
    :return: Page: A page object with the results of the query
    :doc-author: Trelent
    """
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
                                   ) -> Page:
    """
    The search_by_like_fields_or function searches for contacts by name, last_name, email or phone.
    It returns a list of contacts that match the search criteria.

    :param query_str: str: Filter the results by a string
    :param user: User: Get the user id from the token
    :param db: Session: Access the database
    :return: Page: A page of contacts that match the search criteria
    :doc-author: Trelent
    """
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
                                    ) -> Page:
    """
    The search_by_like_fields_and function searches for contacts by the given fields.
        The search is case insensitive and will return all contacts that match any of the given fields.
        If no field is provided, it will return None.

    :param part_name: str | None: Search by name
    :param part_last_name: str | None: Filter the contacts by last name
    :param part_email: str | None: Search for a part of the email
    :param part_phone: int | None: Search by phone number
    :param user: User: Check if the user is logged in
    :param db: Session: Access the database
    :return: Page: A page object
    :doc-author: Trelent
    """
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
                                                     ) -> Page:
    """
    The search_by_birthday_celebration_within_days function searches for contacts whose birthday is within a given
    number of days.

    :param meantime: int: Get the number of days in which we want to search for birthdays
    :param user: User: Get the user_id from the user object
    :param db: Session: Pass the database session to the function
    :return: Page: A paginated list of contacts with birthdays within the given number of days
    :doc-author: Trelent
    """
    today = date.today()
    days_limit = date.today() + timedelta(meantime)
    slide = 1 if days_limit.year - today.year else 0

    return paginate(
                    db.query(Contact)
                    .filter(Contact.user_id == user.id)
                    .filter(func.to_char(Contact.birthday, f'{slide}MM-DD') >= today.strftime(f'0%m-%d'),
                            func.to_char(Contact.birthday, '0MM-DD') <= days_limit.strftime(f'{slide}%m-%d'))
                    )
