from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import Round, Ticket
from schemas import TicketIn, StoreResults
from auth import verify_jwt, require_scope
from utils import make_qr_image
from sqlalchemy import desc
from fastapi.responses import HTMLResponse
import uuid
import logging

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Loto API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200",
                   "https://loto-frontend-site.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_active_round(db: Session):
    return db.query(Round).filter(Round.closed == False).order_by(desc(Round.started_at)).first()


def get_last_round(db: Session):
    return db.query(Round).order_by(desc(Round.started_at)).first()


@app.get("/protected")
async def protected(request: Request):
    payload = await verify_jwt(request)
    return {"message": "Authorized!", "user": payload.get("sub")}


@app.post("/new-round", status_code=204)
async def new_round(payload=Depends(verify_jwt), db: Session = Depends(get_db)):
    require_scope(payload, "manage:rounds")
    active = get_active_round(db)
    if active:
        return
    r = Round(closed=False)
    db.add(r)
    db.commit()


@app.post("/close", status_code=204)
async def close_round(payload=Depends(verify_jwt), db: Session = Depends(get_db)):
    require_scope(payload, "manage:rounds")
    round = get_active_round(db)
    if not round:
        return
    round.closed = True
    db.commit()


@app.post("/store-results", status_code=204)
async def store_results(data: StoreResults, payload=Depends(verify_jwt), db: Session = Depends(get_db)):
    require_scope(payload, "write:results")
    current = get_last_round(db)
    if not current or not current.closed or current.results:
        raise HTTPException(status_code=400, detail="Invalid round state")
    current.results = data.numbers
    db.commit()


@app.post("/tickets")
async def create_ticket(
    data: TicketIn,
    payload=Depends(verify_jwt),
    db: Session = Depends(get_db)
):

    round = get_active_round(db)
    if not round:
        raise HTTPException(
            status_code=400, detail="No active round for betting"
        )

    ticket = Ticket(
        round_id=round.id,
        owner_id=data.owner_id,
        numbers=data.numbers
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    qr_url = f"https://loto-backend-zd7t.onrender.com/ticket/{ticket.id}"
    return make_qr_image(qr_url)


@app.get("/ticket-status")
async def get_ticket_status(db: Session = Depends(get_db)):
    """Get current round status and ticket count"""
    active_round = get_active_round(db)
    last_round = get_last_round(db)

    if not active_round and not last_round:
        return {
            "active_round": None,
            "ticket_count": 0,
            "results": None
        }

    if active_round:
        ticket_count = db.query(Ticket).filter(
            Ticket.round_id == active_round.id).count()
        return {
            "active_round": {
                "id": str(active_round.id),
                "started_at": active_round.started_at.isoformat(),
                "closed": active_round.closed
            },
            "ticket_count": ticket_count,
            "results": None
        }
    else:
        ticket_count = db.query(Ticket).filter(
            Ticket.round_id == last_round.id).count()
        return {
            "active_round": None,
            "ticket_count": ticket_count,
            "results": last_round.results
        }


@app.get("/ticket/{ticket_id}", response_class=HTMLResponse)
async def get_ticket(ticket_id: uuid.UUID, db: Session = Depends(get_db)):
    """Javno dostupna stranica koja prikazuje podatke s listića i izvučene brojeve."""

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    round = db.query(Round).filter(Round.id == ticket.round_id).first()

    ticket_numbers = sorted(ticket.numbers)
    drawn_numbers = sorted(round.results) if round.results else None

    matches = None
    match_count = None
    if drawn_numbers:
        matches = set(ticket_numbers) & set(drawn_numbers)
        match_count = len(matches)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="hr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Loto Listić - {ticket_id}</title>
        <style>
            :root {{
                --color-primary: #33808d;
                --color-background: #fcfcf9;
                --color-surface: #fffffd;
                --color-text: #13343b;
                --color-border: rgba(94, 82, 64, 0.2);
                --color-success: #33808d;
                --color-warning: #e68161;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--color-background);
                color: var(--color-text);
                line-height: 1.6;
                padding: 20px;
            }}
            
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: var(--color-surface);
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04);
                padding: 30px;
            }}
            
            h1 {{
                color: var(--color-primary);
                font-size: 24px;
                margin-bottom: 20px;
                text-align: center;
            }}
            
            .section {{
                margin-bottom: 25px;
                padding-bottom: 25px;
                border-bottom: 1px solid var(--color-border);
            }}
            
            .section:last-child {{
                border-bottom: none;
            }}
            
            .label {{
                font-weight: 600;
                color: var(--color-text);
                margin-bottom: 8px;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .value {{
                font-size: 16px;
                color: var(--color-text);
            }}
            
            .numbers {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 10px;
            }}
            
            .number {{
                width: 45px;
                height: 45px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                font-weight: 600;
                font-size: 18px;
            }}
            
            .number.ticket {{
                background: var(--color-primary);
                color: white;
            }}
            
            .number.drawn {{
                background: var(--color-success);
                color: white;
            }}
            
            .number.match {{
                background: #28a745;
                color: white;
                box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.3);
            }}
            
            .status {{
                text-align: center;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
                font-weight: 600;
            }}
            
            .status.pending {{
                background: rgba(168, 75, 47, 0.1);
                color: var(--color-warning);
                border: 1px solid rgba(168, 75, 47, 0.25);
            }}
            
            .match-info {{
                text-align: center;
                padding: 20px;
                background: rgba(40, 167, 69, 0.1);
                border-radius: 8px;
                margin-top: 20px;
                border: 2px solid rgba(40, 167, 69, 0.3);
            }}
            
            .match-info h2 {{
                color: #28a745;
                font-size: 20px;
                margin-bottom: 10px;
            }}
            
            .ticket-id {{
                font-family: monospace;
                font-size: 12px;
                color: #777;
                text-align: center;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎰 Loto 6/45 - Pregled Listića</h1>
            
            <div class="section">
                <div class="label">Broj osobne / putovnice</div>
                <div class="value">{ticket.owner_id}</div>
            </div>
            
            <div class="section">
                <div class="label">Vaši odabrani brojevi</div>
                <div class="numbers">
                    {''.join(f'<div class="number ticket{" match" if matches and num in matches else ""}">{num}</div>' for num in ticket_numbers)}
                </div>
            </div>
            
            {f'''
            <div class="section">
                <div class="label">Izvučeni brojevi</div>
                <div class="numbers">
                    {''.join(f'<div class="number drawn">{num}</div>' for num in drawn_numbers)}
                </div>
            </div>
            
            <div class="match-info">
                <h2>🎉 Pogođeno brojeva: {match_count}/6</h2>
                {f'<p style="margin-top: 10px;">Pogođeni brojevi: {", ".join(map(str, sorted(matches)))}</p>' if matches else '<p style="margin-top: 10px;">Nažalost, niste pogodili niti jedan broj.</p>'}
            </div>
            ''' if drawn_numbers else '''
            <div class="status pending">
                ⏳ Izvlačenje još nije obavljeno
            </div>
            '''}
            
            <div class="ticket-id">
                ID listića: {ticket_id}
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)
