# This file makes the 'agents' directory a Python package.
# It will also be used to import the instantiated agents.

from .account_agent import account_agent
from .transaction_agent import transaction_agent
from .card_agent import card_agent
from .exchange_rate_agent import exchange_rate_agent

# List of agent names for the supervisor
agent_names = ["account_agent", "transaction_agent", "card_agent", "exchange_rate_agent"]

# Dictionary mapping names to agent runnables for the graph builder
agent_map = {
    "account_agent": account_agent,
    "transaction_agent": transaction_agent,
    "card_agent": card_agent,
    "exchange_rate_agent": exchange_rate_agent,
}