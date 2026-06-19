import logging

from fastapi import Body, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import API_KEY
from app.database import fetch_call_records, save_call_record
from app.models import (
    AgentTurnRequest,
    CallProcessRequest,
    CallRecord,
    CarrierRequest,
    LoadSearchRequest,
    NegotiationRequest,
)
from app.services.call_flow import process_inbound_call
from app.services.agent import handle_agent_turn, start_agent_session
from app.services.fmcsa import verify_carrier
from app.services.loads import get_load_by_id, load_catalog, search_loads
from app.services.negotiation import negotiate_offers
from app.services.transcript import enrich_record_from_transcript

app = FastAPI(
    title="HappyRobot Carrier Sales API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    logging.error(
        "422 on %s -> errors=%s | body=%s",
        request.url.path,
        exc.errors(),
        str(exc.body)[:800],
    )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body_received": str(exc.body)[:800]},
    )


def auth(x_api_key: str = Header(...)):

    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )


@app.get("/health")
def health(x_api_key: str = Header(...)):

    auth(x_api_key)

    return {
        "status": "running",
        "service": "carrier-sales-api",
    }


@app.get("/loads")
def list_loads(x_api_key: str = Header(...)):

    auth(x_api_key)
    return load_catalog()


@app.get("/loads/{load_id}")
def load_detail(load_id: str, x_api_key: str = Header(...)):

    auth(x_api_key)
    load = get_load_by_id(load_id)

    if not load:
        raise HTTPException(status_code=404, detail="Load not found.")

    return load


@app.post("/loads/search")
def search_available_loads(
    request: LoadSearchRequest,
    x_api_key: str = Header(...),
):

    auth(x_api_key)

    return {
        "results": search_loads(
            origin=request.origin,
            destination=request.destination,
            equipment_type=request.equipment_type,
            max_results=request.max_results,
        )
    }


@app.post("/carriers/verify")
def carrier(
    request: CarrierRequest,
    x_api_key: str = Header(...),
):

    auth(x_api_key)
    return verify_carrier(request.mc_number)


@app.post("/negotiations/evaluate")
def negotiation(
    request: NegotiationRequest,
    x_api_key: str = Header(...),
):

    auth(x_api_key)
    load = get_load_by_id(request.load_id)

    if not load:
        raise HTTPException(status_code=404, detail="Load not found.")

    return negotiate_offers(
        load["loadboard_rate"],
        request.offers,
    )


@app.post("/calls/process")
def process_call(
    request: CallProcessRequest,
    x_api_key: str = Header(...),
):

    auth(x_api_key)
    return process_inbound_call(request)


@app.post("/calls/record")
def record(
    payload: dict = Body(...),
    x_api_key: str = Header(...),
):

    auth(x_api_key)
    enriched = enrich_record_from_transcript(payload)
    call_record = CallRecord(**enriched)
    record_id = save_call_record(call_record.dict())

    return {
        "saved": True,
        "record_id": record_id,
        "outcome": call_record.outcome.value,
        "final_rate": call_record.final_rate,
        "mc_number": call_record.mc_number,
        "load_id": call_record.load_id,
    }


@app.get("/calls")
def list_calls(
    x_api_key: str = Header(...),
    limit: int = Query(default=100, ge=1, le=500),
):

    auth(x_api_key)
    return {
        "records": fetch_call_records(limit=limit)
    }


@app.post("/agent/session")
def create_agent_session(x_api_key: str = Header(...)):

    auth(x_api_key)
    return start_agent_session()


@app.post("/agent/respond")
def agent_respond(
    request: AgentTurnRequest,
    x_api_key: str = Header(...),
):

    auth(x_api_key)
    response = handle_agent_turn(
        request.session_id,
        request.utterance,
    )

    if "error" in response:
        raise HTTPException(status_code=404, detail=response["error"])

    return response
