"""The wired services the routes use, built once by the composition root."""

from dataclasses import dataclass

from capper.accounts.service import AccountService
from capper.auth.service import DemoSessionIssuer, TokenVerifier
from capper.conversation.runner import TurnRunner
from capper.conversation.service import ConversationService
from capper.conversation.stop import StopRegistry
from capper.health.service import HealthService


@dataclass(frozen=True)
class Services:
    accounts: AccountService
    conversations: ConversationService
    runner: TurnRunner
    stops: StopRegistry
    verifier: TokenVerifier
    demo_sessions: DemoSessionIssuer
    health: HealthService
