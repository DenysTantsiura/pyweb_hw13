from unittest.mock import MagicMock
from my_module import ProductionClass

thing = ProductionClass()
thing.method = MagicMock(return_value=3)
thing.method(1, 2, 3, key='value')

thing.method.assert_called_with(1, 2, 3, key='value')
