from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.routers.AgentRoutes import router

app = FastAPI(title="CodeMedic API")

app.include_router(router, prefix="/api")

# orig_origins = [
#     "http://localhost:4200",
# ]
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=orig_origins,  # List of allowed origins
#     allow_credentials=True,
#     allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
#     allow_headers=["*"]  # Allow all headers
# )

@app.get("/")
async def root():
    return {"message": "Welcome to CodeMedic API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
