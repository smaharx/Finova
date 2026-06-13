# Finova API Contract

## Status
- Implemented: transaction CRUD, correction loop, analytics summary
- Planned: forecast, anomaly endpoints as dedicated API routes if not yet fully separated

---

## POST /predict-category

Predict a transaction category from description.

### Request
```json
{
  "description": "CHATGPT PLUS"
}
```
### Response
```json
{
  "description": "CHATGPT PLUS",
  "predicted_category": "Subscriptions"
}
```
### Status Codes
- 200 OK
- 503 Service Unavailable if model is not loaded

## POST /transactions

Create a transaction and auto-categorize it.

### Request
```json
{
  "date": "2026-01-01",
  "description": "Netflix",
  "amount": 20.0
}
```
### Response
```json
{
  "message": "Transaction successfully committed to cloud database.",
  "data": {
    "id": 1,
    "date": "2026-01-01",
    "description": "Netflix",
    "category": "Subscriptions",
    "amount": 20.0,
    "is_anomaly": 0
  }
}
```
### Status Codes
- 200 OK
- 500 Internal Server Error

## GET /transactions

Fetch transactions, with optional filters.

### Query Params
- limit
- search
- category
- only_anomalies
- start_date
- end_date
- Response

### Response
```json
{
  "count": 1,
  "transactions": [
    {
      "id": 1,
      "date": "2026-01-01",
      "description": "Netflix",
      "category": "Subscriptions",
      "amount": 20.0,
      "is_anomaly": 0
    }
  ]
}
```
## PUT /transactions/{id}

Update a transaction.

### Request
```json
{
  "date": "2026-01-02",
  "description": "Netflix Premium",
  "amount": 25.0,
  "category": "Subscriptions"
}
```
### Response
```json
{
  "message": "Transaction updated successfully.",
  "data": {
    "id": 1,
    "date": "2026-01-02",
    "description": "Netflix Premium",
    "category": "Subscriptions",
    "amount": 25.0,
    "is_anomaly": 0
  }
}
```
## DELETE /transactions/{id}

Delete a transaction.

### Response
```json
{
  "message": "Transaction deleted successfully.",
  "deleted_id": 1
}
```
## POST /transactions/{id}/correction

Save a correction for a bad AI prediction.

### Request
``` json
{
  "corrected_category": "Subscriptions",
  "notes": "Monthly software plan"
}
```
### Response
```json
{
  "message": "Correction saved successfully."
}
```
## GET /corrections

Fetch recent correction history.

### Response
```json
{
  "count": 1,
  "corrections": [
    {
      "id": 1,
      "transaction_id": 1,
      "original_description": "ChatGPT Plus",
      "predicted_category": "Food",
      "corrected_category": "Subscriptions",
      "notes": "Monthly software plan",
      "created_at": "2026-01-01T12:00:00Z"
    }
  ]
}
```
## GET /analytics/summary

Fetch spending totals and category breakdown.

### Response
```json
{
  "overall": {
    "total_spent": 1500.0,
    "transaction_count": 25
  },
  "categorical_breakdown": [
    {
      "category": "Food",
      "total_amount": 400.0,
      "transaction_count": 8,
      "percentage": 26.67
    }
  ]
}
```
