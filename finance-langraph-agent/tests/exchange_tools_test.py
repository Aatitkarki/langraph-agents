
from src.agents.exchange_rate_agent import get_exchange_rates


exchangeData = get_exchange_rates.invoke({"args": ["USD", "EUR"]})