from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, procedure, dentist
from core.config import settings
from db.database import engine, Base
import models


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title= "OdontoLink",
    description= "Api para projeto de TCC do curso de Análise e Desenvolvimento de Sistemas da Unifoa",
    version= "1.0.0",
    docs_url= "/docs",
    redoc_url= "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(procedure.router)
app.include_router(dentist.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)
  