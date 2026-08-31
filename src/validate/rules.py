def rules_positive_price(df):
    neg_prices  = df[df["price"]<0].copy()
