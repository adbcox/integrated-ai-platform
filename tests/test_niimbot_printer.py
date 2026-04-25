import unittest
from unittest.mock import patch

class TestNiimbotPrinter(unittest.TestCase):

    @patch('niimbot_printer.printer')
    def test_print_labels(self, mock_printer):
        # Arrange
        labels = ["label1", "label2", "label3"]
        
        # Act
        niimbot_printer.print_labels(labels)
        
        # Assert
        mock_printer.assert_called_with("label1")
        mock_printer.assert_called_with("label2")
        mock_printer.assert_called_with("label3")

if __name__ == '__main__':
    unittest.main()
