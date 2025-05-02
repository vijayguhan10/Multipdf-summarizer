import unittest
from Summarization import summarize_text, summarize_multiple_documents, filter_terms_and_conditions, get_summary_from_extracted_text

class TestSummarization(unittest.TestCase):
    def test_summarize_text(self):
        # Test with valid text
        text = "This is a test text for summarization."
        result = summarize_text(text)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

        # Test with empty text
        empty_result = summarize_text("")
        self.assertEqual(empty_result, "No text provided for summarization.")

        # Test with invalid input type
        with self.assertRaises(TypeError):
            summarize_text(None)

        # Test with very long text
        long_text = "This is a very long text. " * 1000
        long_result = summarize_text(long_text)
        self.assertIsInstance(long_result, str)
        self.assertTrue(len(long_result) > 0)

    def test_summarize_multiple_documents(self):
        # Test with valid combined text
        combined_text = "Document 1 content. Document 2 content."
        result = summarize_multiple_documents(combined_text)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

        # Test with empty text
        empty_result = summarize_multiple_documents("")
        self.assertEqual(empty_result, "No text provided for summarization.")

        # Test with invalid document list
        with self.assertRaises(TypeError):
            summarize_multiple_documents("Doc1", None)

        # Test with mixed content types
        mixed_result = summarize_multiple_documents("Doc1. 12345. Special characters: @#$%^&*()")
        self.assertIsInstance(mixed_result, str)
        self.assertTrue(len(mixed_result) > 0)

    def test_filter_terms_and_conditions(self):
        # Test with text containing terms and conditions
        text = "Main content. Terms and conditions: Some legal text."
        filtered_text = filter_terms_and_conditions(text)
        self.assertNotIn("Terms and conditions", filtered_text)

        # Test with multiple terms sections
        multi_terms_text = "Content. Terms: Legal. More content. Conditions: More legal."
        multi_filtered = filter_terms_and_conditions(multi_terms_text)
        self.assertNotIn("Terms", multi_filtered)
        self.assertNotIn("Conditions", multi_filtered)

        # Test with no terms section
        no_terms_text = "Just regular content without any legal text."
        no_terms_filtered = filter_terms_and_conditions(no_terms_text)
        self.assertEqual(no_terms_filtered, no_terms_text)

    def test_get_summary_from_extracted_text(self):
        # Test single document summary
        extracted_text = "This is extracted text."
        result = get_summary_from_extracted_text(extracted_text)
        self.assertIsInstance(result, dict)
        self.assertIn("original_text", result)
        self.assertIn("summary", result)

        # Test multiple document summary
        multi_result = get_summary_from_extracted_text("Doc1. Doc2.", ["doc1.pdf", "doc2.pdf"], True)
        self.assertIsInstance(multi_result, dict)
        self.assertIn("original_text", multi_result)
        self.assertIn("summary", multi_result)

        # Test with missing document names
        with self.assertRaises(ValueError):
            get_summary_from_extracted_text("Doc1. Doc2.", None, True)

        # Test with empty document list
        empty_list_result = get_summary_from_extracted_text("Doc1. Doc2.", [], True)
        self.assertIsInstance(empty_list_result, dict)
        self.assertIn("original_text", empty_list_result)
        self.assertIn("summary", empty_list_result)

if __name__ == '__main__':
    unittest.main()