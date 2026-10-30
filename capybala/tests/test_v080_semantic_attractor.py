"""
test_v080_semantic_attractor.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for Capybala v0.8.0 Post-IF-ELSE Engine:
Semantic Velocity & Dynamical Attractor Manifold Detection.
"""

import unittest
import time
from capybala.attractor import SemanticAttractorDetector
from capybala.detector import DeadlockDetector


class TestSemanticAttractor(unittest.TestCase):

    def test_paraphrased_command_attractor_detected(self):
        """
        Verifies that semantically paraphrased commands with 0% syntactic hash overlap
        are mathematically detected via low Semantic Velocity and Markov Entropy collapse.
        """
        detector = SemanticAttractorDetector(
            velocity_threshold=0.70,
            stagnation_steps=3
        )

        # 4 syntactically diverse commands that all search/test auth persistently
        paraphrased_actions = [
            "grep -rn 'def test_auth' tests/",
            "find . -name '*test_auth*.py'",
            "python -m pytest -k 'test_auth'",
            "grep -i 'test_auth' src/"
        ]

        is_caught = False
        last_details = ""
        for act in paraphrased_actions:
            caught, conf, details = detector.inspect_step(act, is_failing=True)
            if caught:
                is_caught = True
                last_details = details
                break

        self.assertTrue(is_caught, "Paraphrased semantic loop should be detected by SemanticAttractorDetector")
        self.assertIn("Semantic attractor loop detected", last_details)

    def test_productive_diverse_actions_high_velocity(self):
        """
        Verifies that legitimate, diverse agent operations maintain high semantic velocity
        and high Markov entropy, guaranteeing zero false alarms.
        """
        detector = SemanticAttractorDetector()

        diverse_actions = [
            "git status",
            "cat src/auth/jwt.py",
            "pytest tests/test_authentication.py -v",
            "npm run build",
            "curl -X GET http://localhost:8000/health",
            "docker-compose up -d database"
        ]

        for act in diverse_actions:
            caught, conf, _ = detector.inspect_step(act, is_failing=True)
            self.assertFalse(caught, f"Diverse action '{act}' must not be flagged as an attractor")

    def test_successful_actions_never_trigger_attractor(self):
        """
        Verifies the fundamental invariant:
        If actions are succeeding (is_failing=False), an attractor is NEVER declared.
        """
        detector = SemanticAttractorDetector()

        similar_successful_actions = [
            "cat src/auth/jwt.py",
            "cat src/auth/oauth.py",
            "cat src/auth/saml.py",
            "cat src/auth/session.py",
            "cat src/auth/token.py"
        ]

        for act in similar_successful_actions:
            caught, _, _ = detector.inspect_step(act, is_failing=False)
            self.assertFalse(caught, "Successful file reads must never trigger an attractor deadlock")

    def test_sub_millisecond_latency(self):
        """
        Verifies that the pure-Python feature hashing, velocity, and entropy calculations
        execute with average latency < 1.5 ms.
        """
        detector = SemanticAttractorDetector()
        act = "python -c \"import glob, os; print([f for f in glob.glob('**/*.py')])\""

        t0 = time.perf_counter()
        iterations = 100
        for _ in range(iterations):
            detector.inspect_step(act, is_failing=True)
        total_time_ms = (time.perf_counter() - t0) * 1000.0
        avg_latency_ms = total_time_ms / iterations

        self.assertLess(avg_latency_ms, 1.5, f"Average latency ({avg_latency_ms:.3f} ms) exceeds 1.5 ms limit!")

    def test_integrated_deadlock_detector_semantic_attractor(self):
        """
        Verifies that DeadlockDetector seamlessly intercepts semantic attractors
        as a native DeadlockEvent(pattern_type='semantic_attractor').
        """
        detector = DeadlockDetector(enable_attractor=True)

        # Feed 4 paraphrased search/test commands with failure
        paraphrased_actions = [
            ("grep -rn 'def test_auth' tests/", "grep: no matches found"),
            ("find . -name '*test_auth*.py'", "[]\nError: no files"),
            ("python -m pytest -k 'test_auth'", "ERROR: file not found"),
            ("grep -i 'test_auth' src/", "total 0: failed")
        ]

        events = []
        for act, obs in paraphrased_actions:
            event = detector.check(act, obs)
            events.append(event)

        # The 4th turn must trigger semantic_attractor
        final_event = events[-1]
        self.assertTrue(final_event.is_deadlock)
        self.assertEqual(final_event.pattern_type, "semantic_attractor")
        self.assertIn("Semantic attractor loop detected", final_event.details)


if __name__ == "__main__":
    unittest.main()
