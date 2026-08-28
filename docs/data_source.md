# Data source classification

## 1) Data type

This file is best classified as structured data.

Why:
- It is stored as a CSV table with a consistent row-and-column layout.
- Each row represents one transaction, and each column has a defined meaning.
- The dataset follows a tabular schema, even though some cells contain missing or invalid entries.

The file is not fully unstructured because it is not free text or an arbitrary document. It is also not semi-structured in the usual sense of JSON logs or nested key-value records; it is a regular spreadsheet-style table with a clear schema.

## 2) Variables in the dataset

The columns are:

- Transaction ID: unique identifier for each sale record.
- Item: product sold (for example, coffee, cake, salad, juice, sandwich, etc.).
- Quantity: number of units purchased in the transaction.
- Price Per Unit: cost of one unit of the item.
- Total Spent: total spend for the transaction.
- Payment Method: method used to pay, such as cash, credit card, or digital wallet.
- Location: where the purchase happened, such as in-store or takeaway.
- Transaction Date: date on which the transaction was recorded.

## 3) Target and candidate features

The most reasonable target variable for a supervised learning task would be:

- Total Spent

This is the numeric outcome that could be predicted from the other variables.

Candidate features would include:

- Item
- Quantity
- Price Per Unit
- Payment Method
- Location
- Transaction Date

These are the variables that could plausibly help explain or predict the amount spent.

Transaction ID is not a useful predictive feature because it is just an identifier and is unique for each row.
