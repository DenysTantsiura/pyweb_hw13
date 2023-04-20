import unittest
from unittest.mock import MagicMock

from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

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
        contacts = [Contact() for _ in range(10)]
        # self.session.query().filter().offset().limit().all.return_value = contacts
        self.session.query().filter().order_by().return_value = contacts
        result = await get_contacts(user=self.user, db=self.session)
        add_pagination(contacts)
        self.assertEqual(result, paginate(contacts))

    
'''
    async def test_get_contact_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_get_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_create_contact(self):
        body = ContactModel(title="test", description="test contact", tags=[1, 2])
        tags = [Tag(id=1, user_id=1), Tag(id=2, user_id=1)]
        self.session.query().filter().all.return_value = tags
        result = await create_contact(body=body, user=self.user, db=self.session)
        self.assertEqual(result.title, body.title)
        self.assertEqual(result.description, body.description)
        self.assertEqual(result.tags, tags)
        self.assertTrue(hasattr(result, "id"))

    async def test_remove_contact_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_remove_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_update_contact_found(self):
        body = ContactUpdate(title="test", description="test contact", tags=[1, 2], done=True)
        tags = [Tag(id=1, user_id=1), Tag(id=2, user_id=1)]
        contact = Contact(tags=tags)
        self.session.query().filter().first.return_value = contact
        self.session.query().filter().all.return_value = tags
        self.session.commit.return_value = None
        result = await update_contact(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_update_contact_not_found(self):
        body = ContactUpdate(title="test", description="test contact", tags=[1, 2], done=True)
        self.session.query().filter().first.return_value = None
        self.session.commit.return_value = None
        result = await update_contact(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertIsNone(result)

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
