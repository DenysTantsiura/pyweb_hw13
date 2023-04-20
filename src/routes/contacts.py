from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi_limiter.depends import RateLimiter
from fastapi_pagination import add_pagination, Page, Params
from fastapi_pagination.bases import RawParams
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from src.database.db_connect import get_db
from src.database.models import Contact, User
from src.repository import contacts as repository_contacts
from src.schemes import ContactModel, ContactResponse, CatToNameModel
from src.services.auth import auth_service

from src.conf.config import settings
from src.services.pagination import PageParams

router = APIRouter(prefix='/contacts')  # tags=['contacts']


# https://pypi.org/project/python-redis-rate-limit/
@router.get(
            '/', 
            description=f'No more than {settings.limit_crit} requests per minute',
            dependencies=[Depends(RateLimiter(times=settings.limit_crit, seconds=60))],  # , pagination_params = PaginationParams(page=1, page_size=10)],
            response_model=Page, tags=['all_contacts']
            )
async def get_contacts(
                       db: Session = Depends(get_db), 
                       current_user: User = Depends(auth_service.get_current_user),
                       pagination_params: RawParams = Depends()
                       ) -> Page:
    """
    The get_contacts function returns a list of contacts for the current user.

    :param db: Session: Pass the database session to the function
    :param current_user: User: Get the user id from the database
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await repository_contacts.get_contacts(current_user, db, pagination_params)

    return contacts


@router.get(
            '/{contact_id}', 
            description=f'No more than {settings.limit_warn} requests per minute',
            dependencies=[Depends(RateLimiter(times=settings.limit_warn, seconds=60))],
            response_model=ContactResponse, tags=['contact']
            )
async def get_contact(
                      contact_id: int = Path(ge=1),
                      db: Session = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)
                      ) -> Optional[Contact]:
    """
    The get_contact function returns a contact by its id.

    :param contact_id: int: Specify the contact id that is passed in from the url
    :param db: Session: Get a database session
    :param current_user: User: Get the current user from the database
    :return: A contact by id
    :doc-author: Trelent
    """
    contact = await repository_contacts.get_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact Not Found')
    
    return contact


@router.post(
             '/', 
             response_model=ContactResponse,  
             description=f'No more than {settings.limit_crit} requests per minute',
             dependencies=[Depends(RateLimiter(times=settings.limit_crit, seconds=60))], 
             status_code=status.HTTP_201_CREATED, tags=['contact']
             )
async def create_contact(
                         body: ContactModel,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)
                         ) -> Contact:
    """
    The create_contact function creates a new contact in the database.

    :param body: ContactModel: Get the data from the request body
    :param db: Session: Get the database session
    :param current_user: User: Get the user_id of the logged in user
    :return: A contact object
    :doc-author: Trelent
    """
    return await repository_contacts.create_contact(body, current_user, db)


@router.put(
            '/{contact_id}', 
            description=f'No more than {settings.limit_crit} requests per minute',
            dependencies=[Depends(RateLimiter(times=settings.limit_crit, seconds=60))],
            response_model=ContactResponse, tags=['contact']
            )
async def update_contact(
                         body: ContactModel,
                         contact_id: int = Path(ge=1), 
                         db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)
                         ) -> Contact:  
    """
    The update_contact function updates a contact in the database.
        The function takes an id, body and db as parameters.
        It returns a Contact object if successful.

    :param body: ContactModel: Receive the data from the request body
    :param contact_id: int: Specify the contact that will be deleted
    :param db: Session: Get the database session
    :param current_user: User: Get the user's id
    :return: The updated contact
    :doc-author: Trelent
    """
    contact = await repository_contacts.update_contact(contact_id, body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact Not Found')

    return contact


@router.delete(
               '/{contact_id}', 
               description=f'No more than {settings.limit_crit} requests per minute',
               dependencies=[Depends(RateLimiter(times=settings.limit_crit, seconds=60))],
               response_model=ContactResponse, tags=['contact']
               )
async def remove_contact(
                         contact_id: int = Path(ge=1),
                         db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)
                         ) -> Optional[Contact]:
    """
    The remove_contact function removes a contact from the database.

    :param contact_id: int: Specify the contact_id of the contact to be deleted
    :param db: Session: Get the database session
    :param current_user: User: Get the user who is making the request
    :return: An optional contact
    :doc-author: Trelent
    """
    contact = await repository_contacts.remove_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact Not Found')
    
    return contact


@router.patch(
              '/{contact_id}/to_name', 
              description=f'No more than {settings.limit_crit} requests per minute',
              dependencies=[Depends(RateLimiter(times=settings.limit_crit, seconds=60))],
              response_model=ContactResponse, tags=['contact']
              )
async def change_name_contact(
                              body: CatToNameModel,
                              contact_id: int = Path(ge=1),
                              db: Session = Depends(get_db),
                              current_user: User = Depends(auth_service.get_current_user)
                              ) -> Optional[Contact]:
    """
    The change_name_contact function changes the name of a contact.
        Args:
            body (CatToNameModel): The new name for the contact.
            contact_id (int): The id of the contact to change.

    :param body: CatToNameModel: Pass the new name of the contact
    :param contact_id: int: Specify the id of the contact that will be updated
    :param db: Session: Get the database session
    :param current_user: User: Get the user id of the current logged in user
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.change_name_contact(body, contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not Found')

    return contact


# ---SEARCH---------------------------------------------------
@router.get(
            '/search_by_birthday_celebration_within_days/{days}', 
            description=f'No more than {settings.limit_warn} requests per minute',
            dependencies=[Depends(RateLimiter(times=settings.limit_warn, seconds=60))],
            response_model=Page, tags=['search']
            )
async def search_by_birthday_celebration_within_days(
                                                     days: int,
                                                     db: Session = Depends(get_db),
                                                     current_user: User = Depends(auth_service.get_current_user)
                                                     ) -> Page:
    """
    The search_by_birthday_celebration_within_days function searches for contacts that have a birthday celebration
    within the specified number of days.

    :param days: int: Determine the number of days within which a contact's birthday is to be celebrated
    :param db: Session: Get the database session
    :param current_user: User: Get the current user from the auth_service
    :return: A list of contacts that have birthdays within the next
    :doc-author: Trelent
    """
    contact = await repository_contacts.search_by_birthday_celebration_within_days(days, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact Not Found')
    
    return contact


# https://fastapi.tiangolo.com/tutorial/query-params/#__tabbed_2_1
@router.get(
            '/search_by_fields_and/', 
            description=f'No more than {settings.limit_warn} requests per minute',
            dependencies=[Depends(RateLimiter(times=settings.limit_warn, seconds=60))],
            response_model=ContactResponse, tags=['search']
            )
async def search_by_fields_and(
                               #  body: ContactQuery,
                               name: str | None = None,
                               last_name: str | None = None,
                               email: str | None = None,
                               phone: int | None = None,
                               db: Session = Depends(get_db),
                               current_user: User = Depends(auth_service.get_current_user)
                               ) -> Optional[Contact]:
    """
    The search_by_fields_and function searches for a contact by name, last_name, email and phone.
        If the contact is found it returns the contact object.
        If no contacts are found it raises an HTTPException with status code 404 Not Found.

    :param name: str | None: Pass the name of the contact to be searched
    :param last_name: str | None: Search by last name
    :param email: str | None: Search by email
    :param phone: int | None: Search by phone number
    :param db: Session: Get the database session, which is used to query the database
    :param current_user: User: Get the user who is making the request
    :return: A list of contacts
    :doc-author: Trelent
    """
    contact = await repository_contacts.search_by_fields_and(name, last_name, email, phone, current_user, db=db)
    # contact = await repository_contacts.search_by_fields_and(body, current_user, db=db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact Not Found')
    
    return contact


@router.get(
            '/search_by_fields_or/{query_str}', 
            description=f'No more than {settings.limit_warn} requests per minute',
            dependencies=[Depends(RateLimiter(times=settings.limit_warn, seconds=60))],
            response_model=Page, tags=['search']
            )
async def search_by_fields_or(
                              query_str: str,
                              db: Session = Depends(get_db),
                              current_user: User = Depends(auth_service.get_current_user)
                              ) -> Page:
    """
    The search_by_fields_or function searches for contacts by a query string.
    The search is performed on the first_name, last_name, and email fields of the contact table.
    If no matches are found, an HTTP 404 Not Found error is raised.

    :param query_str: str: Search for a contact by name, email or phone number
    :param db: Session: Create a connection to the database
    :param current_user: User: Get the current user
    :return: A list of contacts
    :doc-author: Trelent
    """
    contact = await repository_contacts.search_by_fields_or(query_str, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact Not Found')
    
    return contact


@router.get(
            '/search_by_like_fields_or/{query_str}', 
            description=f'No more than {settings.limit_warn} requests per minute',
            dependencies=[Depends(RateLimiter(times=settings.limit_warn, seconds=60))],
            response_model=Page, tags=['search']
            )
async def search_by_like_fields_or(
                                   query_str: str,
                                   db: Session = Depends(get_db),
                                   current_user: User = Depends(auth_service.get_current_user)
                                   ) -> Page:
    """
    The search_by_like_fields_or function searches for contacts by a query string.
    The search is performed on the first_name, last_name, and email fields of the contact table.
    The search is case insensitive and will return all contacts that match any of the three fields.

    :param query_str: str: Search for a contact by first name, last name, or email
    :param db: Session: Access the database
    :param current_user: User: Get the user's id
    :return: A page object
    :doc-author: Trelent
    """
    contact = await repository_contacts.search_by_like_fields_or(query_str, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact Not Found')
    
    return contact


@router.get(
            '/search_by_like_fields_and/', 
            description=f'No more than {settings.limit_warn} requests per minute',
            dependencies=[Depends(RateLimiter(times=settings.limit_warn, seconds=60))],
            response_model=Page, tags=['search']
            )
async def search_by_like_fields_and(
                                    name: str | None = None,
                                    last_name: str | None = None,
                                    email: str | None = None,
                                    phone: int | None = None,
                                    db: Session = Depends(get_db),
                                    current_user: User = Depends(auth_service.get_current_user)
                                    ) -> Page:
    """
    The search_by_like_fields_and function searches for a contact by name, last_name, email or phone.
        The search is case insensitive and will return all contacts that match the query.

    :param name: str | None: Search for a contact by name
    :param last_name: str | None: Search by last_name,
    :param email: str | None: Search by email
    :param phone: int | None: Filter the contacts by phone
    :param db: Session: Get the database session from the dependency injection
    :param current_user: User: Get the current user from the database
    :return: A list of contacts
    :doc-author: Trelent
    """
    contact = await repository_contacts.search_by_like_fields_and(name, last_name, email, phone, current_user, db=db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact Not Found')
    
    return contact


add_pagination(router)
