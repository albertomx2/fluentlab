"""Validate the exercise bank without opening a database or calling services."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_constants():
    constants = {}
    tree = ast.parse((ROOT / "app.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"LESSONS", "EXERCISES"}:
                    constants[target.id] = ast.literal_eval(node.value)
    return constants


class ContentTests(unittest.TestCase):
    def test_lessons_cover_third_and_both_mixed_conditionals(self):
        lessons = load_constants()["LESSONS"]
        ids = [item["id"] for item in lessons]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue({"zero", "first", "second", "third", "mixed-past-present", "mixed-present-past"}.issubset(ids))

    def test_exercises_reference_valid_lessons_and_have_answers(self):
        constants = load_constants()
        lessons = {item["id"] for item in constants["LESSONS"]}
        exercises = constants["EXERCISES"]
        ids = [item["id"] for item in exercises]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual({item["level"] for item in exercises}, {"B1", "B2", "C1", "C2"})
        for item in exercises:
            with self.subTest(exercise=item["id"]):
                self.assertIn(item["lesson"], lessons)
                self.assertTrue(item["prompt"])
                self.assertTrue(item["answers"])
                self.assertTrue(item["explanation"])
                if item.get("options"):
                    self.assertTrue(set(item["answers"]).issubset(item["options"]))


if __name__ == "__main__":
    unittest.main()
