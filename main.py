from fastapi import FastAPI
from routes import indexroute, cameraaccessroute,hrroute, staticroute
from database import create_db_and_tables
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware


app = FastAPI()
create_db_and_tables()

# app.add_middleware(HTTPSRedirectMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(indexroute.router)
app.include_router(cameraaccessroute.router)
app.include_router(hrroute.router)
app.include_router(staticroute.router)



