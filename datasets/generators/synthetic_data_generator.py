import random
import pandas as pd


def generate_synthetic_transactions(num_rows: int = 100) -> pd.DataFrame:
    """Generate synthetic transactions data for validation stress testing."""
    statuses = ["COMPLETED", "PENDING", "FAILED", None]
    data = []
    for i in range(1, num_rows + 1):
        data.append({
            "transaction_id": i,
            "customer_id": random.randint(1000, 1050),
            "amount": round(random.uniform(10.0, 5000.0), 2) if random.random() > 0.1 else None,
            "status": random.choice(statuses)
        })
    return pd.DataFrame(data)


if __name__ == "__main__":
    df = generate_synthetic_transactions(50)
    df.to_csv("datasets/fixtures/sample_transactions.csv", index=False)
    print("Generated 50 synthetic records to datasets/fixtures/sample_transactions.csv")
