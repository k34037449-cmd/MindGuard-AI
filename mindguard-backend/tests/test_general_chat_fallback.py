"""Offline fallback regression tests. Run: python -m unittest discover -s tests"""
import unittest

from ai_engine.llm_connector import _general_chat_fallback
from ai_engine.general_chat import _fallback_timetable, _validate_timetable


class GeneralChatFallbackTests(unittest.TestCase):
    def reply(self, message):
        return _general_chat_fallback([{"role": "user", "content": message}])

    def test_arithmetic(self):
        self.assertIn("= 4", self.reply("What is 2 + 2?"))

    def test_greeting(self):
        self.assertIn("Ask me anything", self.reply("Hi"))

    def test_motivation(self):
        self.assertIn("15 minutes", self.reply("Motivate me"))

    def test_photosynthesis_explanation(self):
        answer = self.reply("Explain photosynthesis")
        self.assertIn("chlorophyll", answer.lower())
        self.assertIn("glucose", answer.lower())

    def test_mindguard_comparison(self):
        answer = self.reply("What is the difference between you and ChatGPT?")
        self.assertIn("student support", answer.lower())
        self.assertIn("general-purpose", answer.lower())

    def test_three_hour_timetable_covers_three_hours_of_focus(self):
        answer = _fallback_timetable("Make a 3 hour timetable")
        self.assertTrue(_validate_timetable(answer, "Make a 3 hour timetable"))
        self.assertIn("21:30", answer)

    def test_explicit_clock_window(self):
        answer = _fallback_timetable("Make a timetable from 6 pm to 10 pm")
        self.assertTrue(_validate_timetable(answer, "Make a timetable from 6 pm to 10 pm"))
        self.assertIn("22:00", answer)


if __name__ == "__main__":
    unittest.main()
