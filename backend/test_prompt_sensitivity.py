import unittest
from unittest.mock import patch

from agent import agent as agent_module


class PromptSensitivityTests(unittest.TestCase):
    def setUp(self):
        agent_module.PERSONAL_EVENT_DRAFTS.clear()
        agent_module.PENDING_PERSONAL_EVENTS.clear()
        agent_module.PENDING_PERSONAL_CONFLICT_CHOICES.clear()
        agent_module.CLARIFICATION_STATE.clear()

    def _minimal_events(self):
        return [
            {
                "id": "101",
                "title": "AI Workshop",
                "date": "2026-03-28",
                "start_time": "11:00",
                "end_time": "13:00",
                "tags": ["tech"],
                "description": "Hands-on AI workshop",
            },
            {
                "id": "102",
                "title": "Career Talk",
                "date": "2026-03-28",
                "start_time": "15:00",
                "end_time": "16:00",
                "tags": ["career"],
                "description": "Resume and interview tips",
            },
        ]

    def _no_conflict_calendar(self):
        return [
            {
                "title": "Morning Gym",
                "date": "2026-03-28",
                "start_time": "06:00",
                "end_time": "07:00",
                "type": "personal",
            }
        ]

    @patch("agent.agent.generate_reply", side_effect=lambda *args, **kwargs: kwargs.get("fallback", "ok"))
    @patch("agent.agent.get_user_profile", return_value={"interests": [], "career_goals": [], "major": ""})
    def test_parser_extracts_day_first_phrase(self, _profile, _reply):
        slots = agent_module._parse_event_slots("add math test to my calendar on 28th march 9pm")
        self.assertEqual(slots["title"], "Math Test")
        self.assertEqual(slots["date"], "2026-03-28")
        self.assertEqual(slots["start_time"], "21:00")
        self.assertEqual(slots["end_time"], "23:00")
        self.assertEqual(slots["missing_fields"], [])

    def test_parser_extracts_month_first_with_noise(self):
        slots = agent_module._parse_event_slots("can you please schedule project demo for march 29th, 10:30 am")
        self.assertEqual(slots["title"], "Project Demo")
        self.assertEqual(slots["date"], "2026-03-29")
        self.assertEqual(slots["start_time"], "10:30")
        self.assertEqual(slots["end_time"], "12:30")

    def test_parser_extracts_numeric_date_and_24h_time(self):
        slots = agent_module._parse_event_slots("pls can u add coding sprint, for 29/03/2026 at 21:15!!!")
        self.assertEqual(slots["title"], "Coding Sprint")
        self.assertEqual(slots["date"], "2026-03-29")
        self.assertEqual(slots["start_time"], "21:15")
        self.assertEqual(slots["end_time"], "23:15")

    def test_parser_extracts_iso_date_and_midnight(self):
        slots = agent_module._parse_event_slots("please add deploy task on 2026-04-02 at midnight")
        self.assertEqual(slots["title"], "Deploy Task")
        self.assertEqual(slots["date"], "2026-04-02")
        self.assertEqual(slots["start_time"], "00:00")
        self.assertEqual(slots["end_time"], "02:00")

    def test_tolerant_parser_recovers_hour_only_time(self):
        slots = agent_module._parse_event_slots("add sprint planning on mar 31 at 21")
        self.assertEqual(slots["title"], "Sprint Planning")
        self.assertEqual(slots["date"], "2026-03-31")
        self.assertEqual(slots["start_time"], "21:00")
        self.assertEqual(slots["end_time"], "23:00")

    def test_tolerant_parser_recovers_tomorrow_shortcut(self):
        slots = agent_module._parse_event_slots("pls add standup tmrw at 9am")
        self.assertEqual(slots["title"], "Standup")
        self.assertTrue(bool(slots["date"]))
        self.assertEqual(slots["start_time"], "09:00")

    def test_parser_reports_missing_fields(self):
        slots = agent_module._parse_event_slots("add coding session")
        self.assertEqual(slots["title"], "Coding Session")
        self.assertIn("date", slots["missing_fields"])
        self.assertIn("time", slots["missing_fields"])

    @patch("agent.agent.generate_reply", side_effect=lambda *args, **kwargs: kwargs.get("fallback", "ok"))
    @patch("agent.agent.get_user_profile", return_value={"interests": [], "career_goals": [], "major": ""})
    def test_one_turn_add_success(self, _profile, _reply):
        response = agent_module.simple_agent(
            user_id="phase5-user-1",
            user_message="add math test to my calendar on 28th march 9pm",
            events=self._minimal_events(),
            calendar=self._no_conflict_calendar(),
        )
        self.assertEqual(response.get("action"), "add_to_calendar")
        event = response.get("event_to_add", {})
        self.assertEqual(event.get("title"), "Math Test")
        self.assertEqual(event.get("date"), "2026-03-28")
        self.assertEqual(event.get("start_time"), "21:00")

    @patch("agent.agent.generate_reply", side_effect=lambda *args, **kwargs: kwargs.get("fallback", "ok"))
    @patch("agent.agent.get_user_profile", return_value={"interests": [], "career_goals": [], "major": ""})
    def test_single_clarify_then_completion(self, _profile, _reply):
        user_id = "phase5-user-2"
        first = agent_module.simple_agent(
            user_id=user_id,
            user_message="add project meeting to my calendar on 28th march",
            events=self._minimal_events(),
            calendar=self._no_conflict_calendar(),
        )
        self.assertEqual(first.get("action"), "clarify")
        self.assertIn("What time", first.get("reply", ""))

        second = agent_module.simple_agent(
            user_id=user_id,
            user_message="9pm",
            events=self._minimal_events(),
            calendar=self._no_conflict_calendar(),
        )
        self.assertEqual(second.get("action"), "add_to_calendar")
        event = second.get("event_to_add", {})
        self.assertEqual(event.get("title"), "Project Meeting")
        self.assertEqual(event.get("start_time"), "21:00")

    @patch("agent.agent.generate_reply", side_effect=lambda *args, **kwargs: kwargs.get("fallback", "ok"))
    @patch("agent.agent.get_user_profile", return_value={"interests": [], "career_goals": [], "major": ""})
    def test_conflict_replace_or_keep_path(self, _profile, _reply):
        user_id = "phase5-user-3"
        conflict_calendar = [
            {
                "title": "Math Test",
                "date": "2026-03-28",
                "start_time": "20:00",
                "end_time": "22:00",
                "type": "personal",
            }
        ]

        initial = agent_module.simple_agent(
            user_id=user_id,
            user_message="add hackathon prep to my calendar on 28th march 9pm",
            events=self._minimal_events(),
            calendar=conflict_calendar,
        )
        self.assertEqual(initial.get("action"), "clarify")
        self.assertIn("Reply 'replace'", initial.get("reply", ""))

        replace_response = agent_module.simple_agent(
            user_id=user_id,
            user_message="replace",
            events=self._minimal_events(),
            calendar=conflict_calendar,
        )
        self.assertEqual(replace_response.get("action"), "replace_conflicting_with_personal")
        self.assertTrue(replace_response.get("conflicting_events"))

        user_id_keep = "phase5-user-4"
        _ = agent_module.simple_agent(
            user_id=user_id_keep,
            user_message="add design review to my calendar on 28th march 9pm",
            events=self._minimal_events(),
            calendar=conflict_calendar,
        )
        keep_response = agent_module.simple_agent(
            user_id=user_id_keep,
            user_message="keep",
            events=self._minimal_events(),
            calendar=conflict_calendar,
        )
        self.assertEqual(keep_response.get("action"), "clarify")
        self.assertIn("kept your existing calendar unchanged", keep_response.get("reply", "").lower())

    @patch("agent.agent.generate_reply", side_effect=lambda *args, **kwargs: kwargs.get("fallback", "ok"))
    @patch("agent.agent.get_user_profile", return_value={"interests": [], "career_goals": [], "major": ""})
    def test_interruption_full_details_overwrite_pending(self, _profile, _reply):
        user_id = "phase5-user-5"
        first = agent_module.simple_agent(
            user_id=user_id,
            user_message="add project review to my calendar on march 28th",
            events=self._minimal_events(),
            calendar=self._no_conflict_calendar(),
        )
        self.assertEqual(first.get("action"), "clarify")

        second = agent_module.simple_agent(
            user_id=user_id,
            user_message="add dentist appointment to my calendar on march 29th 5pm",
            events=self._minimal_events(),
            calendar=self._no_conflict_calendar(),
        )
        self.assertEqual(second.get("action"), "add_to_calendar")
        event = second.get("event_to_add", {})
        self.assertEqual(event.get("title"), "Dentist Appointment")
        self.assertEqual(event.get("date"), "2026-03-29")
        self.assertEqual(event.get("start_time"), "17:00")

    @patch("agent.agent.get_user_profile", return_value={"interests": [], "career_goals": [], "major": ""})
    def test_no_duplicate_clarification_for_same_missing_state(self, _profile):
        user_id = "phase5-user-6"
        first = agent_module.simple_agent(
            user_id=user_id,
            user_message="add meeting",
            events=self._minimal_events(),
            calendar=self._no_conflict_calendar(),
        )
        self.assertEqual(first.get("action"), "clarify")

        second = agent_module.simple_agent(
            user_id=user_id,
            user_message="hmm",
            events=self._minimal_events(),
            calendar=self._no_conflict_calendar(),
        )
        self.assertEqual(second.get("action"), "clarify")
        self.assertNotEqual(first.get("reply"), second.get("reply"))
        self.assertIn("need", second.get("reply", "").lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
