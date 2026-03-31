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
   pip install flask pymongo
   ```
3. (Optional) Set MongoDB URI:
   ```bash
   set MONGO_URI=mongodb://localhost:27017
   ```
4. Run the API:
   ```bash
   python app1.py
   ```

## API
- `GET /` health check
- `GET /api/lottery?date=YYYY-MM-DD&limit=10` get results by date

Default port: `8080`
