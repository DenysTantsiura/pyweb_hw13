from datetime import date
import unittest
from unittest.mock import MagicMock
from fastapi import HTTPException

from fastapi_pagination import Page, Params
from pydantic import EmailStr
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
from src.schemes import ContactModel, CatToNameModel


class TestContacts(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        cls.TEST_RANGE = 12
        cls.PAGE = 1
        cls.SIZE = 10
        cls.meantime = 8
        cls.query_str = 'nown1'
        cls.name = 'New_Name'
        cls.last_name = 'Last_name'
        cls.phone = 123
        cls.email = 'Unknown2@mail.com'  # 'New_email@mail.com'
        cls.user = User(id=1)
        cls.contact = Contact(
                              user_id=1,  # cls.user 
                              id=1, 
                              name='Unknown2', 
                              last_name='Unknown2', 
                              email=EmailStr('Unknown2@mail.com'),  # ='Unknown2@mail.com'
                              phone=1,
                              birthday=date.today(),
                              description='...',
                              user=cls.user
                              )
        cls.body = ContactModel(
                                name='Unknown2', 
                                last_name='Unknown2', 
                                email=EmailStr('Unknown2@mail.com'), 
                                phone=1, 
                                birthday=date.today(), 
                                description='...'
                                )
        cls.contacts = [Contact(
                                id=i+1, 
                                name=f'nown{i}',   # name=f'nown1{i}', 
                                email=EmailStr(f'Unknown{i+1}@mail.com'),
                                birthday=date.today()
                                )
                        for i in range(TestContacts.TEST_RANGE)]
 
    @staticmethod
    def part_string_in_dictionary_values(query_str: str, current_dict: dict):
        return [query_str for el in current_dict.values() if query_str in str(el)]

    def setUp(self):
        """
         створюємо об'єкт MagicMock для заміни об'єкта Session у модульних тестах MagicMock(spec=Session).
         У цьому випадку, MagicMock використовується для створення "фіктивного" об'єкта Session, 
         а використання параметра spec=Session у конструкторі MagicMock вказує, що створюваний об'єкт 
         матиме ті самі атрибути і методи, що й об'єкт Session
        """
        self.session = MagicMock(spec=Session)
        # self.user = User(id=1)

    async def test_get_contacts(self):
        self.session.query.return_value.filter.return_value.order_by.return_value.count.return_value = TestContacts.SIZE
        self.session.query().filter().order_by().limit().offset().all.return_value = TestContacts.contacts
        result = await get_contacts(
                                    user=self.user,
                                    db=self.session,
                                    pagination_params=Params(page=TestContacts.PAGE, size=TestContacts.SIZE)
                                    )
        self.assertIsInstance(result, Page)
        self.assertEqual(result.page, TestContacts.PAGE)
        self.assertEqual(result.total, TestContacts.SIZE)
        self.assertEqual(len(result.items), TestContacts.TEST_RANGE)
        [self.assertEqual(result.items[i].email, f'Unknown{i+1}@mail.com') for i in range(len(result.items))]
     
    async def test_get_contact_found(self):
        self.session.query().filter().filter_by().first.return_value = TestContacts.contact
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result, TestContacts.contact)
        [self.assertEqual(result.__dict__[el], TestContacts.contact.__dict__[el])
            for el in TestContacts.contact.__dict__]

    async def test_get_contact_not_found(self):
        self.session.query().filter().filter_by().first.return_value = None
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_create_contact(self):
        self.session.query().filter().filter_by().first.return_value = None
        result = await create_contact(body=TestContacts.body, user=self.user, db=self.session)
        [self.assertEqual(result.__dict__[el], TestContacts.body.__dict__[el]) for el in TestContacts.body.__dict__]
        self.assertTrue(hasattr(result, "id"))

    async def test_create_contact_dublicat(self):
        self.session.query().filter().filter_by().first.return_value = TestContacts.contact
        with self.assertRaises(HTTPException) as context:
            await create_contact(body=TestContacts.body, user=self.user, db=self.session)
        self.assertTrue(context.exception)

    async def test_remove_contact_found(self):
        self.session.query().filter().filter_by().first.return_value = TestContacts.contact
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result, TestContacts.contact)

    async def test_remove_contact_not_found(self):
        self.session.query().filter().filter_by().first.return_value = None
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_update_contact_found(self):
        self.session.query().filter().filter_by().first.return_value = TestContacts.contact
        self.session.commit.return_value = None
        result = await update_contact(contact_id=1, body=TestContacts.body, user=self.user, db=self.session)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result, TestContacts.contact)

    async def test_update_contact_not_found(self):
        self.session.query().filter().filter_by().first.return_value = None
        self.session.commit.return_value = None
        result = await update_contact(contact_id=1, body=TestContacts.body, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_change_name_contact(self):
        body = CatToNameModel(name='New_Name')
        self.session.query().filter().filter_by().first.return_value = TestContacts.contact
        self.session.commit.return_value = None
        result = await change_name_contact(body=body, contact_id=1, user=self.user, db=self.session)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result, TestContacts.contact)

    async def test_search_by_fields_and_not_found(self):
        self.session.query().filter().filter_by().filter_by().filter_by().filter_by().first.return_value = None
        result = await search_by_fields_and(
                                            name=TestContacts.name, 
                                            last_name=TestContacts.last_name, 
                                            email=TestContacts.email, 
                                            phone=TestContacts.phone, 
                                            user=self.user, 
                                            db=self.session
                                            )
        self.assertIsNone(result)

    async def test_search_by_fields_and_found(self):
        self.session.query().filter().filter_by().filter_by().first.return_value = TestContacts.contact
        result = await search_by_fields_and(
                                            name=TestContacts.name, 
                                            last_name=None, 
                                            email=TestContacts.email, 
                                            phone=None, 
                                            user=self.user, 
                                            db=self.session
                                            )
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.name, TestContacts.name)
        self.assertEqual(result.email, TestContacts.email)
        self.assertEqual(result, TestContacts.contact)

    async def test_search_by_fields_or_found(self):
        self.session.query.return_value.filter.return_value.filter.return_value.count.return_value = TestContacts.SIZE
        sample = [contact
                  for contact in TestContacts.contacts
                  if TestContacts.part_string_in_dictionary_values(TestContacts.query_str, contact.__dict__)]
        self.session.query().filter().filter().limit().offset().all.return_value = sample
        result = await search_by_fields_or(
                                           query_str=TestContacts.query_str, 
                                           user=self.user, 
                                           db=self.session,
                                           pagination_params=Params(page=TestContacts.PAGE, size=TestContacts.SIZE)
                                           )
        self.assertIsInstance(result, Page)
        self.assertEqual(result.page, TestContacts.PAGE)
        self.assertEqual(result.total, TestContacts.SIZE)
        self.assertEqual(len(result.items), 5)  # 10? TEST_RANGE // 10 + 1 because "query_str = 'nown1'"

    async def test_search_by_fields_or_not_found(self):
        self.session.query.return_value.filter.return_value.filter.return_value.count.return_value = TestContacts.SIZE
        self.session.query().filter().filter().limit().offset().all.return_value = []
        result = await search_by_fields_or(
                                           query_str=TestContacts.query_str, 
                                           user=self.user, 
                                           db=self.session,
                                           pagination_params=Params(page=TestContacts.PAGE, size=TestContacts.SIZE)
                                           )
        self.assertIsInstance(result, Page)
        self.assertEqual(result.page, TestContacts.PAGE)
        self.assertEqual(result.total, TestContacts.SIZE)
        self.assertEqual(result.items, [])

    async def test_search_by_like_fields_or_found(self):
        self.session.query.return_value.filter.return_value.filter.return_value.count.return_value = TestContacts.SIZE
        sample = [contact
                  for contact in TestContacts.contacts
                  if TestContacts.part_string_in_dictionary_values(TestContacts.query_str, contact.__dict__)]
        self.session.query().filter().filter().limit().offset().all.return_value = sample
        result = await search_by_like_fields_or(
                                                query_str=TestContacts.query_str, 
                                                user=self.user, 
                                                db=self.session,
                                                pagination_params=Params(page=TestContacts.PAGE, size=TestContacts.SIZE)
                                                )
        self.assertIsInstance(result, Page)
        self.assertEqual(result.page, TestContacts.PAGE)
        self.assertEqual(result.total, TestContacts.SIZE)
        self.assertEqual(len(result.items), 5)  # TestContacts.TEST_RANGE

    async def test_search_by_like_fields_or_not_found(self):  
        self.session.query.return_value.filter.return_value.filter.return_value.count.return_value = TestContacts.SIZE
        self.session.query().filter().filter().limit().offset().all.return_value = []
        result = await search_by_like_fields_or(
                                                query_str=TestContacts.query_str, 
                                                user=self.user, 
                                                db=self.session,
                                                pagination_params=Params(page=TestContacts.PAGE, size=TestContacts.SIZE)
                                                )
        self.assertIsInstance(result, Page)
        self.assertEqual(result.page, TestContacts.PAGE)
        self.assertEqual(result.total, TestContacts.SIZE)
        self.assertEqual(result.items, [])

    async def test_search_by_like_fields_and_found(self):
        self.session.query().filter().filter().filter().count.return_value = TestContacts.SIZE
        self.session.query().filter().filter().filter().limit().offset().all.return_value = TestContacts.contacts
        result = await search_by_like_fields_and(
                                                 part_name=TestContacts.name, 
                                                 part_last_name=None, 
                                                 part_email=TestContacts.email, 
                                                 part_phone=None, 
                                                 user=self.user, 
                                                 db=self.session,
                                                 pagination_params=Params(
                                                                          page=TestContacts.PAGE,
                                                                          size=TestContacts.SIZE
                                                                          )
                                                 )
        self.assertIsInstance(result, Page)
        self.assertEqual(result.page, TestContacts.PAGE)
        self.assertEqual(result.total, TestContacts.SIZE)
        self.assertEqual(len(result.items), TestContacts.TEST_RANGE)

    async def test_search_by_like_fields_and_not_found(self):
        self.session.query().filter().filter().filter().filter().filter().count.return_value = TestContacts.SIZE
        self.session.query().filter().filter().filter().filter().filter().limit().offset().all.return_value = []
        result = await search_by_like_fields_and(
                                                 part_name=TestContacts.name, 
                                                 part_last_name=TestContacts.last_name, 
                                                 part_email=TestContacts.email, 
                                                 part_phone=TestContacts.phone, 
                                                 user=self.user, 
                                                 db=self.session,
                                                 pagination_params=Params(
                                                                          page=TestContacts.PAGE,
                                                                          size=TestContacts.SIZE
                                                                          )
                                                 )
        self.assertIsInstance(result, Page)
        self.assertEqual(result.page, TestContacts.PAGE)
        self.assertEqual(result.total, TestContacts.SIZE)
        self.assertEqual(result.items, [])

    async def test_search_by_birthday_celebration_within_days_found(self):
        self.session.query.return_value.filter.return_value.filter.return_value.count.return_value = TestContacts.SIZE
        self.session.query().filter().filter().limit().offset().all.return_value = TestContacts.contacts
        result = await search_by_birthday_celebration_within_days(
                                                                  meantime=TestContacts.meantime,
                                                                  user=self.user, 
                                                                  db=self.session,
                                                                  pagination_params=Params(
                                                                                           page=TestContacts.PAGE,
                                                                                           size=TestContacts.SIZE
                                                                                           )
                                                                  )
        self.assertIsInstance(result, Page)
        self.assertEqual(result.page, TestContacts.PAGE)
        self.assertEqual(result.total, TestContacts.SIZE)
        self.assertEqual(len(result.items), TestContacts.TEST_RANGE)

    async def test_search_by_birthday_celebration_within_days_not_found(self):
        self.session.query.return_value.filter.return_value.filter.return_value.count.return_value = TestContacts.SIZE
        self.session.query().filter().filter().limit().offset().all.return_value = []
        result = await search_by_birthday_celebration_within_days(
                                                                  meantime=TestContacts.meantime,
                                                                  user=self.user, 
                                                                  db=self.session,
                                                                  pagination_params=Params(
                                                                                           page=TestContacts.PAGE,
                                                                                           size=TestContacts.SIZE
                                                                                           )
                                                                  )
        self.assertIsInstance(result, Page)
        self.assertEqual(result.page, TestContacts.PAGE)
        self.assertEqual(result.total, TestContacts.SIZE)
        self.assertEqual(result.items, [])


if __name__ == '__main__':
    unittest.main()
