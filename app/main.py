from fastapi import FastAPI

from app.routers import auth, centres, bookings

app = FastAPI(title="EVE Healthcare Booking API")

app.include_router(auth.router)
app.include_router(centres.router)
app.include_router(bookings.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
