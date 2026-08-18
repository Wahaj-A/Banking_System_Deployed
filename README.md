# 🏦 Apex Capital Bank — AI-Powered Banking CRM

> A full-stack banking CRM application combining core banking operations with live weather, cryptocurrency market data, AI assistants, policy-aware RAG, and backend application logging.

---

## 📌 Overview

**Apex Capital Bank** is a full-stack banking CRM built with a React frontend and a Python/FastAPI backend.

The application provides traditional banking operations alongside real-time external data and AI-powered assistants. Users can manage banking activities, view transaction history, check live weather for five supported cities, monitor five live cryptocurrency assets, and interact with specialized AI agents.

The project is designed with a clear separation between the frontend, backend APIs, external data sources, AI agents, and application logging.

---

## ✨ Key Features

### 🏦 Banking CRM

- User signup and login
- Create bank accounts
- View account information
- View account balances
- Deposit funds
- Withdraw funds
- Transfer funds
- Transaction history
- View all accounts

### 🤖 AI Banking Assistant

- Natural-language banking conversations
- Banking-related assistance through an AI agent
- Backend-powered AI processing
- Separate policy/RAG assistant for banking information

### 📚 Banking Policy RAG

- Uses the bank's policy/terms document as a knowledge source
- Provides policy-aware answers
- Uses retrieval-augmented generation concepts
- Keeps policy information separate from general banking-agent conversations

### 🌤️ Live Weather

The application supports exactly **five cities**:

1. Lahore
2. Karachi
3. Islamabad
4. Peshawar
5. Quetta

Features include:

- Live current weather
- Temperature
- Feels-like temperature
- Humidity
- Wind speed
- Precipitation
- 5-day forecast
- Manual city selection
- Automatic refresh every 10 minutes
- Manual Refresh button
- AI Weather Agent

**Weather provider:** Open-Meteo

No weather API key is required.

### ₿ Live Cryptocurrency Data

The application supports exactly **five assets**:

1. Bitcoin (BTC)
2. Ethereum (ETH)
3. BNB
4. Solana (SOL)
5. XRP

Features include:

- Live market price
- 24-hour market information
- Manual asset selection
- Automatic refresh every 60 seconds
- Manual Refresh button
- AI Crypto Agent
- Live-data tool usage by the AI agent

**Market data provider:** Binance public 24-hour ticker endpoint

No crypto API key is required for the public endpoints.

### 📝 Application Logging

The backend includes centralized application logging for:

- HTTP requests
- Response status codes
- Response time
- Authentication events
- Account operations
- Deposits
- Withdrawals
- Transfers
- Weather requests
- Crypto requests
- AI-agent requests
- Errors and exceptions

Logs are written to the console and to a rotating log file.

Sensitive information such as passwords and API keys is intentionally excluded from application logs.

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────┐
│              React Frontend                │
│          Vite + React + Tailwind           │
└──────────────────────┬──────────────────────┘
                       │
                       │ HTTP / JSON
                       ▼
┌─────────────────────────────────────────────┐
│             FastAPI Backend                 │
│                                             │
│  Banking │ Weather │ Crypto │ AI │ RAG     │
└──────────┬──────────────┬──────────────┬────┘
           │              │              │
           ▼              ▼              ▼
      Banking DB      Open-Meteo       Binance

                       │
                       ▼
                 Gemini AI Agents

                       │
                       ▼
                Application Logger
                       │
                       ▼
                  logs/app.log
```

---

## 🛠️ Technology Stack

### Frontend

- React 18
- Vite
- Tailwind CSS
- Recharts

### Backend

- Python
- FastAPI
- Uvicorn
- Python-dotenv

### AI

- Google Gemini / `google-genai`
- Gemini-powered banking assistant
- Gemini-powered Weather Agent
- Gemini-powered Crypto Agent
- RAG-based banking policy assistant

### RAG / Retrieval

- LangChain Community
- LangChain Text Splitters
- LangChain HuggingFace
- FAISS

### Data

- SQLite
- Pandas

### External APIs

- Open-Meteo — weather
- Binance public ticker endpoint — cryptocurrency market data

---

## 📁 Project Structure

```text
Loggs/
│
├── Backend/
│   ├── main.py
│   ├── bank_logic.py
│   ├── agent_logic.py
│   ├── rag_agent.py
│   ├── rag_test.py
│   ├── weather.py
│   ├── weather_agent.py
│   ├── crypto.py
│   ├── crypto_agent.py
│   ├── logger.py
│   ├── hbl_terms.txt
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   └── logs/
│
├── Frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── WEATHER_FEATURE.md
│   └── CRYPTO_FEATURE.md
│
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

Replace `YOUR-USERNAME/YOUR-REPOSITORY` with your GitHub repository.

---

## ⚙️ Backend Setup

Open a terminal in the Backend directory:

```bash
cd Backend
```

### Create a virtual environment

#### Windows

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use:

```powershell
.\venv\Scripts\activate.bat
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a file named:

```text
Backend/.env
```

Add:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

You can use `.env.example` as a template.

> ⚠️ Never commit your real `.env` file or API key to GitHub.

### Start the backend

```bash
python main.py
```

The backend runs at:

```text
http://127.0.0.1:8000
```

---

## 💻 Frontend Setup

Open a second terminal:

```bash
cd Frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend normally runs at:

```text
http://localhost:5173
```

---

## 🔌 Main API Endpoints

### Authentication

```text
POST /api/signup
POST /api/login
```

### Banking

```text
GET  /api/accounts
GET  /api/accounts/{account_id}
GET  /api/accounts/{account_id}/transactions
POST /api/accounts
POST /api/deposit
POST /api/withdraw
POST /api/transfer
```

### Banking AI / RAG

```text
POST /api/agent/chat
POST /api/rag/ask
```

### Weather

```text
GET  /api/weather/cities
GET  /api/weather/{city}
POST /api/weather/ask
```

### Cryptocurrency

```text
GET  /api/crypto/currencies
GET  /api/crypto/{asset}
POST /api/crypto/ask
```

---

## 🌤️ Changing the Supported Weather Cities

The five supported cities are controlled by the `SUPPORTED_CITIES` dictionary in:

```text
Backend/weather.py
```

To change the cities, update their names and coordinates there.

The same supported-city configuration is used by the weather functionality and AI weather agent.

---

## ₿ Changing Supported Crypto Assets

The supported cryptocurrency assets are defined by the backend crypto implementation.

The current project supports:

```text
BTC
ETH
BNB
SOL
XRP
```

The frontend and AI crypto agent use the supported asset list rather than allowing arbitrary unsupported assets.

---

## 📝 Logging

Application logs are written to:

```text
Backend/logs/app.log
```

The logger also outputs information to the backend terminal.

Example:

```text
2026-08-17 13:20:10 | INFO | apex_bank | AUTH login successful
2026-08-17 13:20:15 | INFO | apex_bank | WEATHER live data request
2026-08-17 13:20:18 | INFO | apex_bank | CRYPTO live market data request
2026-08-17 13:20:22 | INFO | apex_bank | AI weather assistant request received
```

The application uses rotating log files to prevent the log file from growing indefinitely.

### Security

The logging system avoids recording sensitive information such as:

- Passwords
- API keys
- Authentication tokens
- Sensitive request bodies

---

## 🔐 Environment Variables

The backend currently requires:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Create your local environment file:

```text
Backend/.env
```

Do not upload it to GitHub.

The repository includes:

```text
Backend/.env.example
```

as a safe template.

---

## 🔄 Live Data Behavior

### Weather

The weather dashboard automatically refreshes every **10 minutes** and also provides a manual Refresh button.

The AI Weather Agent retrieves live weather information before answering current-weather questions.

### Cryptocurrency

The crypto dashboard automatically refreshes every **60 seconds** and also provides a manual Refresh button.

The AI Crypto Agent uses the live crypto market-data tool for current market questions.

> Live market and weather information can change continuously. A displayed value represents the latest data retrieved by the application at that time.

---

## 🧪 Development Commands

### Backend

```bash
python main.py
```

### Frontend

```bash
npm run dev
```

### Frontend production build

```bash
npm run build
```

### Preview production build

```bash
npm run preview
```

---

## 🔒 Security Notes

For a production deployment, additional security hardening would be recommended.

At minimum:

- Keep API keys in environment variables.
- Never commit `.env`.
- Never log passwords or secrets.
- Use HTTPS in production.
- Add proper authentication/session management.
- Validate and sanitize API inputs.
- Apply rate limiting to public endpoints.
- Use a production-grade database and migration strategy.
- Restrict CORS appropriately for the deployed frontend domain.
- Review authorization rules for every banking operation.

---

## 📈 Future Improvements

Potential improvements include:

- Production authentication with secure sessions/JWT
- Role-based access control
- PostgreSQL or another production database
- Advanced transaction analytics
- More detailed financial dashboards
- Streaming/live market updates
- More weather locations
- Notification system
- Automated testing
- CI/CD pipeline
- Docker deployment
- Cloud deployment
- Centralized production log monitoring
- Improved AI response citations and observability

---

## 🎯 Project Highlights

This project demonstrates practical integration of:

- Full-stack web development
- REST API development
- React frontend development
- FastAPI backend development
- Database-backed banking operations
- External API integration
- Real-time data retrieval
- AI agents
- Function/tool calling
- Retrieval-Augmented Generation
- Application logging
- Frontend/backend separation
- Environment-based configuration

---

## 👨‍💻 Author

**Wahaj Ahmed**

This project was developed as a practical full-stack banking CRM application with AI, live data integrations, and backend observability.

---

## 📄 License

This project is intended for educational, internship, and portfolio purposes unless otherwise specified by the project owner.
