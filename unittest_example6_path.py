from unittest.mock import patch


# examples:

# всередині контексту замінили метод method класу ProductionClass на mock реалізацію
with patch.object(ProductionClass, 'method', return_value=3) as mock_method:
    thing = ProductionClass()
    thing.method(1, 2, 3)
    mock_method.assert_called_once_with(1, 2, 3)


# ---- or -------

# замінили в модулі module два класи ClassName2 і ClassName1 на mock-реалізації. 
# Звісно, що модуль module повинен існувати для цього
"""використовуємо декоратор @patch, щоб замінити вихідні класи ClassName1 і ClassName2 у модулі module 
на мок-об'єкти MockClass1 і MockClass2 відповідно. Декоратори передадуть їх як параметри функції test_class
"""
@patch('module.ClassName2')
@patch('module.ClassName1')
def test_class(MockClass1, MockClass2):
    # викликаємо вихідні класи ClassName1 і ClassName2, які насправді замінені на мок-об'єкти
    module.ClassName1()
    module.ClassName2()
    # перевіряємо, що заміна відбулася успішно, порівнюючи значення MockClass1 і MockClass2 
    # з оригінальними класами ClassName1 і ClassName2
    assert MockClass1 is module.ClassName1
    assert MockClass2 is module.ClassName2
    # перевіряємо, чи були викликані мок-об'єкти, використовуючи атрибут called
    assert MockClass1.called
    assert MockClass2.called
