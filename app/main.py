from fastapi import FastAPI

app = FastAPI(title="EVE Healthcare Booking API")


@app.get("/health")
def health_check():
    return {"status": "ok"}
