from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.routers.AgentRoutes import router

app = FastAPI(title="CodeMedic API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to CodeMedic API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
