from fastapi import FastAPI
from routes import router
import uvicorn

app = FastAPI(title="CodeMedic API")

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to CodeMedic API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
