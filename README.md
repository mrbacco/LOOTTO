# LOOTTO

Quick Flask API for lottery results using MongoDB.

## Files
- `app1.py`: main Flask API
- `app.py`: alternate script
- `Lotto.csv`: lottery data source

## Quick Start
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install flask pymongo python-dotenv
   ```
3. Configure MongoDB Atlas (recommended):
   - Create a `.env` file in the project root.
   - Add your Atlas credentials and URI, for example:
     ```env
     MONGO_URI=mongodb+srv://mrbacco04_db_user:wdTWUwfeVRB7aIlD@cluster0.cxzgfix.mongodb.net/?appName=Cluster0
     ```
4. Run the API:
   ```bash
   python app1.py
   ```

## Notes
- `app1.py` now reads `MONGO_URI` from `.env` or from the environment.
- If `MONGO_URI` is not set, it falls back to your Atlas URI by default.
- Default port: `8000`

## API
- `GET /` health check
- `GET /api/lottery?date=YYYY-MM-DD&limit=10` get results by date
- `GET /api/lottery/<draw_date>` fetch a single lottery result by draw date
- `POST /api/lottery` create a new lottery result
- `PUT /api/lottery/<draw_date>` update an existing result
- `DELETE /api/lottery/<draw_date>` delete a result

### POST /api/lottery JSON payload
```json
{
  "drawDate": "2026-05-08",
  "num1": "01",
  "num2": "02",
  "num3": "03",
  "num4": "04",
  "num5": "05",
  "num6": "06",
  "strong": "07"
}
```
