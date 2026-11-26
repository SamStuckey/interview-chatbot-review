"""Accounts has no specs of its own: its service is thin queries with no logic to test alone.

Its behavior is covered where it's used: token verification and the demo sign-in
(`tests/capper/auth/`), the account context and local time in a turn
(`tests/capper/conversation/test_runner.py`), and the seeded users and referral codes
(`tests/scripts/test_seed.py`).
"""
