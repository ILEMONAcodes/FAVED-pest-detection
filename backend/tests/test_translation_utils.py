import json
import unittest

from translation_utils import normalize_translation, parse_translation


class TranslationUtilsTests(unittest.TestCase):
    def setUp(self):
        self.complete = {
            "description": "Bayanin cutar.",
            "cause": "Ruwan sama yana taimaka wa cutar.",
            "more_about": "Cutar na yaduwa cikin sauri.",
            "steps": ["Cire 'ya'yan da suka kamu."],
            "prevention": ["Datsa rassan bishiyar."],
            "pathogen": "Phytophthora palmivora",
        }

    def test_parses_json_fenced_response(self):
        raw = "```json\n{" + '"description": "a", "cause": "b", "more_about": "c", "steps": ["d"], "prevention": ["e"]' + "}\n```"

        parsed = parse_translation(raw)

        self.assertEqual(parsed["description"], "a")

    def test_parses_json_with_leading_commentary(self):
        raw = "Here is the translation:\n" + json.dumps(self.complete)

        self.assertEqual(parse_translation(raw), self.complete)

    def test_normalizes_whitespace_and_discards_non_string_list_items(self):
        translated = dict(self.complete, steps=["  Mataki daya.  ", None, "" ])

        result = normalize_translation(translated)

        self.assertEqual(result["steps"], ["Mataki daya."])
        self.assertEqual(result["pathogen"], "Phytophthora palmivora")

    def test_rejects_missing_or_empty_advice_fields(self):
        incomplete = dict(self.complete, prevention=[])

        self.assertIsNone(normalize_translation(incomplete))

    def test_rejects_non_object_json(self):
        self.assertIsNone(parse_translation('["not", "an object"]'))


if __name__ == "__main__":
    unittest.main()
