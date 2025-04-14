import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.exchange_rate_agent import get_exchange_rates

def main():
    try:
        print("Running exchange tools test...")
        exchangeData = get_exchange_rates.invoke({"currency_codes": ["USD"]})
        print("Test completed successfully!")
        print("Result:", exchangeData)
    except Exception as e:
        print("Test failed with error:")
        print(type(e).__name__, ":", str(e))

if __name__ == "__main__":
    main()