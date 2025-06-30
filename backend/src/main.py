import logging
from fastapi import FastAPI

# Configure FastAPI logging
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

app = FastAPI() 