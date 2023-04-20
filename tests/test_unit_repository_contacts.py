from datetime import date
import unittest
from unittest.mock import MagicMock
from fastapi import HTTPException, status

from fastapi_pagination import add_pagination, Params
from fastapi_pagination.bases import RawParams
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import EmailStr
from sqlalchemy.orm import Session

from src.services.pagination import PageParams
from src.database.models import Contact, User
from src.repository.contacts import (
    get_contacts,
    get_contact,
    create_contact,
    update_contact,
    remove_contact,
    change_name_contact,
    search_by_fields_and,
    search_by_fields_or,
    search_by_like_fields_or,
    search_by_like_fields_and,
    search_by_birthday_celebration_within_days,
    )
from src.schemes import ContactModel, ContactResponse, CatToNameModel


class TestContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        """
         створюємо об'єкт MagicMock для заміни об'єкта Session у модульних тестах MagicMock(spec=Session).
         У цьому випадку, MagicMock використовується для створення "фіктивного" об'єкта Session, 
         а використання параметра spec=Session у конструкторі MagicMock вказує, що створюваний об'єкт 
         матиме ті самі атрибути і методи, що й об'єкт Session
        """
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_get_contacts(self):
        contacts = [Contact() for _ in range(30)]
        # self.session.query().filter().offset().limit().all.return_value = contacts
        self.session.query().filter().order_by().return_value = contacts
        result = await get_contacts(user=self.user, db=self.session, pagination_params=RawParams(offset=1, limit=10))  # page=1, size=10
        # add_pagination(contacts)
        self.assertEqual(result, paginate(contacts, RawParams(offset=1, limit=10)))

    
    async def test_get_contact_found(self):
        contact = Contact(
                          user_id=self.user, 
                          id=1, 
                          name='AB', 
                          last_name='AB', 
                          email='qwerty@com.com',
                          phone=3,
                          birthday=date.today(),
                          description='...',
                          user=self.user
                          )  
        self.session.query().filter().filter_by().first.return_value = contact
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_get_contact_not_found(self):
        self.session.query().filter().filter_by().first.return_value = None
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_create_contact(self):
        body = ContactModel(
                            name='Unknown2', 
                            last_name='Unknown2', 
                            email=EmailStr('Unknown2@mail.com'), 
                            phone=1, 
                            birthday=date.today(), 
                            description='-2'
                            )
        self.session.query().filter().filter_by().first.return_value = None
        result = await create_contact(body=body, user=self.user, db=self.session)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)
        self.assertEqual(result.description, body.description)
        self.assertTrue(hasattr(result, "id"))

    async def test_create_contact_dublicat(self):
        body = ContactModel(
                            name='Unknown2', 
                            last_name='Unknown2', 
                            email=EmailStr('Unknown2@mail.com'), 
                            phone=1, 
                            birthday=date.today(), 
                            description='-2'
                            )
        contact = Contact(
                          user_id=self.user, 
                          id=1, 
                          name='Unknown2', 
                          last_name='Unknown2', 
                          email='Unknown2@mail.com',
                          phone=1,
                          birthday=date.today(),
                          description='-2',
                          user=self.user
                          )
        self.session.query().filter().filter_by().first.return_value = contact
        with self.assertRaises(HTTPException) as context:
            result = await create_contact(body=body, user=self.user, db=self.session)
        self.assertTrue(context.exception)

    async def test_remove_contact_found(self):
        contact = Contact()
        self.session.query().filter().filter_by().first.return_value = contact
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_remove_contact_not_found(self):
        self.session.query().filter().filter_by().first.return_value = None
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)


    async def test_update_contact_found(self):
        body = ContactModel(
                            name='Unknown2', 
                            last_name='Unknown2', 
                            email=EmailStr('Unknown2@mail.com'), 
                            phone=1, 
                            birthday=date.today(), 
                            description='-2'
                            )
        contact = Contact(
                          user_id=self.user, 
                          id=1, 
                          name='AB', 
                          last_name='AB', 
                          email='qwerty@com.com',
                          phone=3,
                          birthday=date.today(),
                          description='...',
                          user=self.user
                          )  
        self.session.query().filter().filter_by().first.return_value = contact
        self.session.commit.return_value = None
        result = await update_contact(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertEqual(result, contact)


    async def test_update_contact_not_found(self):
        body = ContactModel(
                            name='Unknown2', 
                            last_name='Unknown2', 
                            email=EmailStr('Unknown2@mail.com'), 
                            phone=1, birthday=date.today(), 
                            description='-2'
                            )
        self.session.query().filter().filter_by().first.return_value = None
        self.session.commit.return_value = None
        result = await update_contact(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertIsNone(result)

'''
    async def test_update_status_contact_found(self):
        body = ContactStatusUpdate(done=True)
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        self.session.commit.return_value = None
        result = await update_status_contact(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_update_status_contact_not_found(self):
        body = ContactStatusUpdate(done=True)
        self.session.query().filter().first.return_value = None
        self.session.commit.return_value = None
        result = await update_status_contact(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertIsNone(result)
'''

if __name__ == '__main__':
    unittest.main()


'''
from fastapi_pagination import PaginationParams

pagination_params = PaginationParams(page=1, page_size=10)

res = get_contacts(session, user, pagination_params)

paginate(db.query(…), pagination_params)

'''
