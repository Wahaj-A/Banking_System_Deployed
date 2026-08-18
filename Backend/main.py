import os
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from pathlib import Path

from Backend.logger import logger

# Import your existing banking and AI logic
from Backend.bank_logic import Bank, Auth
from Backend import agent_logic
from Backend import rag_agent
from Backend import weather
from Backend import weather_agent
from Backend import crypto
from Backend import crypto_agent

# Load local .env for development. Vercel supplies environment variables directly.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def get_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured on the server.")
    return api_key

# Initialize the FastAPI application
app = FastAPI(title="AI Banking CRM API")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log API method/path/status/duration without request bodies."""
    started = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "HTTP %s %s -> %s (%.1f ms)",
            request.method, request.url.path, response.status_code, duration_ms
        )
        return response
    except Exception:
        duration_ms = (time.perf_counter() - started) * 1000
        logger.exception(
            "Unhandled exception during %s %s (%.1f ms)",
            request.method, request.url.path, duration_ms
        )
        raise


# Configure CORS so the React frontend can talk to this backend
app.add_middleware(
    CORSMiddleware,
  allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://banking-crm-weather-crypto-zyug.vercel.app",  # Your frontend domain
    "https://banking-crm-weather-crypto-lvkz.vercel.app",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Bank and Auth classes
bank = Bank()
auth = Auth()

# ==========================================
# 📦 PYDANTIC MODELS (Data Validation)
# ==========================================
class UserCredentials(BaseModel):
    email: str
    password: str

class AccountCreate(BaseModel):
    name: str
    email: str
    starting_balance: float = 0.0

class Transaction(BaseModel):
    account_id: int
    amount: float
    email: str  # <--- NEW: Requires email for verification

class Transfer(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float
    email: str  # <--- NEW: Requires email for verification

class RAGQuery(BaseModel):
    question: str

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    text: str


class WeatherAgentMessage(BaseModel):
    user_text: str
    history: List[ChatMessage] = []

class CryptoAgentMessage(BaseModel):
    user_text: str
    history: List[ChatMessage] = []

class AgentChat(BaseModel):
    user_text: str
    history: List[ChatMessage] = []
    email: str  # <--- Added to receive the email from the frontend

# ==========================================
# 🔐 AUTHENTICATION ENDPOINTS
# ==========================================
@app.post("/api/signup")
def signup(req: UserCredentials):
    try:
        auth.signup(req.email, req.password)
        logger.info("AUTH signup successful")
        return {"message": "Account created"}
    except ValueError as e:
        logger.warning("AUTH signup failed")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/login")
def login(req: UserCredentials):
    try:
        email = auth.login(req.email, req.password)
        logger.info("AUTH login successful")
        return {"email": email}
    except ValueError as e:
        logger.warning("AUTH login failed")
        raise HTTPException(status_code=401, detail=str(e))

# ==========================================
# 🏦 BANKING ENDPOINTS
# ==========================================
@app.get("/api/accounts")
def get_accounts():
    accounts = bank.list_accounts()
    return [
        {
            "account_id": a.account_id, 
            "account_number": a.account_number, 
            "name": a.name, 
            "balance": a.balance
        } 
        for a in accounts
    ]

@app.get("/api/accounts/{account_id}")
def get_account(account_id: int, email: str):
    acc = bank.find_account(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
        
    # 🔒 SECURITY CHECK: Ensure account belongs to logged-in user
    if acc.email != email:
        raise HTTPException(status_code=403, detail="Permission Denied: You can only view your own account balance.")
        
    return {"account_id": acc.account_id, "account_number": acc.account_number, "name": acc.name, "balance": acc.balance}

@app.get("/api/accounts/{account_id}/transactions")
def get_transactions(account_id: str, email: str):
    acc = bank.find_account(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
        
    if acc.email != email:
        raise HTTPException(status_code=403, detail="Permission Denied: You can only view your own transaction history.")
        
    # Since bank_logic.py already formats this as a list of dictionaries,
    # we can safely return it directly to the frontend!
    history = bank.get_transaction_history(account_id)
    return history


@app.post("/api/accounts")
def create_account(req: AccountCreate):
    try:
        acc = bank.create_account(req.name, req.starting_balance, req.email)
        logger.info("BANK account created successfully")
        return {"message": "Success", "account_id": acc.account_id, "balance": acc.balance, "account_number": acc.account_number}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/deposit")
def deposit(req: Transaction):
    try:
        acc = bank.find_account(req.account_id)
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")
            
        # 🔒 SECURITY CHECK: Compare email to email!
        if acc.email != req.email:
            raise HTTPException(status_code=403, detail="Permission Denied: You can only deposit into your own account.")
            
        acc = bank.deposit(req.account_id, req.amount)
        logger.info("BANK deposit completed successfully")
        return {"message": "Success", "new_balance": acc.balance, "name": acc.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/api/withdraw")
def withdraw(req: Transaction):
    try:
        # 🚨 FIX 1: Removed req.email from the arguments
        acc = bank.find_account(req.account_id)
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")
            
        # 🚨 FIX 2: Compare email to email!
        if acc.email != req.email:
            raise HTTPException(status_code=403, detail="Permission Denied: You can only withdraw from your own account.")

        acc = bank.withdraw(req.account_id, req.amount)
        logger.info("BANK withdrawal completed successfully")
        return {"message": "Success", "new_balance": acc.balance, "name": acc.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/transfer")
def transfer(req: Transfer):
    try:
        # 🚨 FIX 3: Removed req.email from the arguments
        sender = bank.find_account(req.from_account_id)
        if not sender:
            raise HTTPException(status_code=404, detail="Sender account not found")
            
        # 🚨 FIX 4: Compare email to email!
        if sender.email != req.email:
            raise HTTPException(status_code=403, detail="Permission Denied: You can only transfer funds out of your own account.")

        sender, receiver = bank.transfer(req.from_account_id, req.to_account_id, req.amount)
        logger.info("BANK transfer completed successfully")
        return {
            "message": "Success", 
            "from_account": {"name": sender.name, "balance": sender.balance},
            "to_account": {"name": receiver.name, "balance": receiver.balance}
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    
# ==========================================
# 🤖 AI AGENT ENDPOINTS
# ==========================================
@app.post("/api/rag/ask")
def ask_policy(req: RAGQuery):
    try:
        logger.info("AI policy assistant request received")
        answer = rag_agent.ask_bank_policy(req.question)
        logger.info("AI policy assistant response generated")
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agent/chat")
def chat_with_agent(req: AgentChat):
    try:
        formatted_history = [(msg.role, msg.text) for msg in req.history]
        
        # 🔒 SECURITY LOCK: Find the user's specific account number based on their email
        current_user_account_number = None
        for acc in bank.list_accounts():
            if acc.email == req.email:
                # 🚨 THE FIX: Pass the 6-digit account_number, not the internal account_id!
                current_user_account_number = acc.account_number
                break
        
        logger.info("AI banking assistant request received")
        response = agent_logic.send_message(
            bank=bank, 
            api_key=get_api_key(), 
            history=formatted_history, 
            user_text=req.user_text,
            user_account_id=current_user_account_number  # Now passes the 6-digit number (e.g., 229161)
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ==========================================
# 🌤️ WEATHER ENDPOINTS
# ==========================================
@app.get("/api/weather/cities")
def get_weather_cities():
    """Return live weather for the five supported cities."""
    try:
        logger.info("WEATHER live data request for all supported cities")
        return {"cities": weather.get_all_weather()}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/weather/{city}")
def get_weather_city(city: str):
    """Return live weather and a five-day forecast for one supported city."""
    try:
        logger.info("WEATHER live data request for one city")
        return weather.get_weather(city)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/api/weather/ask")
def ask_weather_agent(req: WeatherAgentMessage):
    """Answer a weather question using live data through the Gemini weather agent."""
    try:
        history = [{"role": msg.role, "text": msg.text} for msg in req.history]
        logger.info("AI weather assistant request received")
        response = weather_agent.ask_weather(
            user_text=req.user_text,
            history=history,
            api_key=get_api_key(),
        )
        return {"response": response}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ₿ CRYPTO ENDPOINTS
# ==========================================
@app.get("/api/crypto/currencies")
def get_crypto_currencies():
    """Return live market data for the five supported cryptocurrencies."""
    try:
        logger.info("CRYPTO live market data request for all supported assets")
        return {"currencies": crypto.get_all_crypto()}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/crypto/{asset}")
def get_crypto_asset(asset: str):
    """Return live 24-hour market data for one supported cryptocurrency."""
    try:
        logger.info("CRYPTO live market data request for one asset")
        return crypto.get_crypto(asset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/api/crypto/ask")
def ask_crypto_agent(req: CryptoAgentMessage):
    """Answer a crypto question using live market data through the Gemini agent."""
    try:
        history = [{"role": msg.role, "text": msg.text} for msg in req.history]
        logger.info("AI crypto assistant request received")
        response = crypto_agent.ask_crypto(
            user_text=req.user_text,
            history=history,
            api_key=get_api_key(),
        )
        return {"response": response}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 🏃‍♂️ SERVER RUNNER
# ==========================================
if __name__ == "__main__":
    import uvicorn
    # Runs the FastAPI server on port 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)