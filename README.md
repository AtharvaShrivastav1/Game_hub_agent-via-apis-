# GameHub — Agentic AI Game Store

**GameHub** is a full-stack proof-of-concept demonstrating an agentic AI game marketplace inspired by Steam aesthetics. GameHub features an embedded AI assistant orchestrated via **LangGraph**, **LangChain**, **FastAPI**, **SQLAlchemy**, **MySQL**, and **React + Vite**, showcasing multi-agent orchestration, controlled database tools, and strict **human-in-the-loop (HITL) approval** for purchases.

---

## 1. Architecture Overview

GameHub employs a clean, decoupled 5-tier architecture that isolates concerns across presentation, routing, agent reasoning, controlled tools, and database persistence:

```text
                            React Frontend (Vite + TypeScript)
                                           │
                                           ▼ (REST / JSON)
                                      FastAPI API
                                           │
                  ┌────────────────────────┴────────────────────────┐
                  ▼                                                 ▼
          Standard REST APIs                                AI Assistant API
                  │                                                 │
                  │                                                 ▼
                  │                                        LangGraph StateGraph
                  │                                                 │
                  │                                         Orchestrator Agent
                  │                                                 │
                  │                          ┌──────────────────────┴──────────────────────┐
                  │                          ▼                                             ▼
                  │                    Research Agent                              Purchase / Validation Agent
                  │                          │                                             │
                  │                          ▼                                             ▼
                  │                 Recommendation Agent                           HITL Approval Gate
                  │                          │                                       [Interrupt / Pause]
                  │                          │                                             │
                  │                          │                                             ▼
                  │                          │                                     Execute Purchase Tool
                  │                          └──────────────────────┬──────────────────────┘
                  │                                                 │
                  ▼                                                 ▼
             Service Layer (GameService, CartService, PurchaseService [ACID Atomic Transactions])
                  │
                  ▼
            Repository Layer (GameRepo, CartRepo, LibraryRepo, UserRepo, PurchaseRepo)
                  │
                  ▼
            SQLAlchemy ORM ──▶ MySQL Database (`gamehub_db`)
```

### Clean Layering Guarantee:
1. **Frontend**: Pure UI presentation, client state, and user actions. Never contains business logic.
2. **API Layer**: Validates requests via Pydantic schemas and delegates to Services or LangGraph workflows.
3. **Agent / LangGraph Layer**: Orchestrates intent classification, database tool calls, and HITL interrupt gates. Never executes raw SQL strings.
4. **Service Layer**: Implements business rules (e.g., duplicate ownership prevention, wallet balance verification, atomic purchase transactions with ACID rollback).
5. **Repository Layer**: Encapsulates SQLAlchemy ORM operations for games, users, carts, purchases, and library records.
6. **Database**: Persistent MySQL database storing structured records.

---

## 2. Multi-Agent System & LangGraph Workflow

The AI assistant operates via a compiled LangGraph `StateGraph` backed by `MemorySaver` checkpointing:

```text
                             [START]
                                │
                                ▼
                       Orchestrator Agent
                        (Intent Router)
                                │
         ┌──────────────────────┼──────────────────────┐
         │ (SEARCH / RECOMMEND  │                      │ (PURCHASE)
         │  / COMPARE / CART)   │                      │
         ▼                      │                      ▼
   Research Agent               │            Purchase / Validation Agent
 (Catalog & Cart Tools)         │           (Pre-validates Wallet & Ownership)
         │                      │                      │
         ▼                      │                      ▼
Recommendation Agent            │            HITL Approval Gate
(Reasoning & Ranking)           │        (Interrupt before execution)
         │                      │                /           \
         │                      │       [Reject]               [Approve]
         │                      │          │                       │
         │                      │          ▼                       ▼
         │                      │        [END]           Execute Purchase Tool
         │                      │                    (Atomic MySQL ACID Transaction)
         │                      │                                  │
         └──────────────────────┼──────────────────────────────────┘
                                │
                                ▼
                              [END]
```

### Agents Breakdown:

1. **Orchestrator Agent (`app/agents/orchestrator.py`)**:
   - Analyzes incoming user messages and classifies intent (`SEARCH`, `RECOMMEND`, `COMPARE`, `CART_QUERY`, `CART_MODIFICATION`, `PURCHASE`, `GENERAL_GAME_QUERY`).
   - Extracts structured constraints (budget, genre, duration, ratings, target game titles) using structured LLM output with deterministic fallback.
   - Conditionally routes state to the appropriate specialist agent.

2. **Game Research Agent (`app/agents/research_agent.py`)**:
   - Queries the GameHub MySQL catalog via controlled tools (`search_games`, `get_game`, `get_user_library`, `get_user_cart`, `get_user_wallet`).
   - Identifies candidate games matching constraints.
   - Excludes games the user already owns to prevent redundant suggestions.

3. **Recommendation Agent (`app/agents/recommendation_agent.py`)**:
   - Reasons strictly over grounded candidates retrieved from the database.
   - Ranks candidates according to user preferences, budget limits, and playtime value.
   - Explains *why* specific titles fit the user's request without hallucinating unlisted games.

4. **Purchase / Validation Agent (`app/agents/purchase_agent.py`)**:
   - Resolves target purchase games (from explicit titles, cart items, or the currently viewed game).
   - Pre-validates user existence, catalog availability, non-ownership, and wallet balance.
   - Prepares a financial `PurchaseSummary` (itemized list, total price, current wallet, remaining balance).
   - Sets up the **Human-in-the-Loop Approval Gate** before any database mutations occur.

---

## 3. Human-in-the-Loop (HITL) Purchase Workflow

The application strictly enforces human authorization for monetary transactions:
1. When a purchase intent is detected (e.g., *"Buy Cyberstrike"* or *"Buy everything in my cart"*), the purchase agent validates all preconditions.
2. The LangGraph workflow reaches an approval interrupt (`interrupt_before=["execute_purchase"]`), pausing the thread in the checkpointer.
3. The API returns `requires_approval: true` along with the structured `approval_data`.
4. The frontend renders the **Purchase Confirmation Modal** and in-chat approval card showing:
   - Selected game title(s)
   - Total purchase cost
   - Available wallet balance
   - Remaining balance after transaction
   - Explicit `[Cancel / Reject]` and `[Approve Purchase]` controls.
5. If **Approved**: The client posts to `/api/purchase/approve`, resuming the thread. The `execute_purchase` node invokes the atomic transaction tool, commits the changes in MySQL, updates the wallet, clears the cart, and adds the game to **My Library**.
6. If **Rejected**: The client posts to `/api/purchase/reject`, cancelling the thread without touching the database.

---

## 4. Controlled Tools

Rather than giving the LLM arbitrary database access, agents interact strictly through controlled tools (`app/tools/game_tools.py`):

| Tool | Parameters | Description |
|---|---|---|
| `search_games` | `genre`, `max_price`, `max_duration`, `min_rating`, `search`, `sort_by` | Controlled catalog filtering |
| `get_game` | `game_id` | Full game metadata retrieval |
| `get_user_library` | `user_id` | Retrieves user's owned games |
| `get_user_cart` | `user_id` | Retrieves cart items and subtotal |
| `get_user_wallet` | `user_id` | Retrieves current wallet balance |
| `add_to_cart` | `user_id`, `game_id` | Adds item, blocking already owned games |
| `remove_from_cart` | `user_id`, `game_id` | Removes item from cart |
| `validate_purchase` | `user_id`, `game_ids` | Pre-transaction validation and summary |
| `purchase_game` | `user_id`, `game_ids` | **Atomic ACID transaction tool** (requires approval) |

---

## 5. Database Schema (MySQL)

```sql
-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    wallet_balance FLOAT NOT NULL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Games table
CREATE TABLE games (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    genre VARCHAR(50) NOT NULL,
    price FLOAT NOT NULL,
    rating FLOAT NOT NULL,
    duration_hours FLOAT NOT NULL,
    developer VARCHAR(150) NOT NULL,
    release_date VARCHAR(50) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Cart Items table
CREATE TABLE cart_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    game_id INT NOT NULL,
    quantity INT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_cart_game (user_id, game_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

-- Purchases table
CREATE TABLE purchases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    game_id INT NOT NULL,
    price FLOAT NOT NULL,
    status VARCHAR(50) DEFAULT 'COMPLETED',
    purchased_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

-- User Game Library table
CREATE TABLE user_game_library (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    game_id INT NOT NULL,
    purchase_id INT,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_library_game (user_id, game_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE SET NULL
);
```

### Atomic Purchase Transaction Guarantee:
```python
# Atomic ACID transaction in app/services/purchase_service.py:
BEGIN TRANSACTION;
  Validate user exists & lock record;
  Verify game exists & check non-ownership;
  Verify wallet_balance >= total_price;
  Deduct wallet_balance;
  Insert Purchase record;
  Insert UserGameLibrary record;
  Delete matching CartItem;
COMMIT;
-- On any exception: ROLLBACK;
```

---

## 6. Setup & Installation

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- MySQL Server (running on port 3306)

### 1. Backend Setup in Virtual Environment
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
# source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Create `backend/.env` (or copy from `backend/.env.example`):
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=gamehub_db

# Application Configuration
PROJECT_NAME="GameHub API"
API_V1_STR="/api"
DEBUG=True

# Gemini / LLM Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.6-flash
GEMINI_TEMPERATURE=0.0
```

### 3. Seed Database
Initialize MySQL tables and populate sample games and demo user:
```bash
python seed.py
```

### 4. Run Automated Tests
```bash
pytest -v tests/
```
All 8 integration tests validate:
- Game search and filtering
- Cart operations
- Duplicate ownership prevention
- Insufficient wallet rollback
- Atomic purchase transaction success
- Orchestrator intent routing
- LangGraph recommendation workflow
- LangGraph Human-in-the-Loop purchase approval interrupt & resume.

---

## 7. Running the Application

### 1. Start FastAPI Backend Server
```bash
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --port 8000 --reload
```
API runs at: `http://localhost:8000`  
Swagger Documentation: `http://localhost:8000/docs`

### 2. Start React Frontend Server
```bash
cd frontend
npm install
npm run dev
```
Web Store UI runs at: `http://localhost:5173`

---

## 8. Demonstration Scenario & Example Prompts

| Step | User Action | Expected System Behavior |
|---|---|---|
| **1. Browse Store** | Navigate `http://localhost:5173/` | Explores game cards, genre tags, and wallet pill showing balance. |
| **2. Contextual AI** | Open *Cyberstrike*, click *"Is this worth buying?"* | AI Assistant opens in contextual mode and evaluates value per hour based on factual game rating. |
| **3. Comparison** | Prompt: *"Compare this with another RPG under ₹2000"* | Orchestrator routes to Research Agent then Recommendation Agent, presenting a comparison table. |
| **4. Budget Recommendation** | Prompt: *"I have ₹3000. Recommend two games under 30 hours."* | Evaluates catalog constraints, filters out owned games, and explains why the selection fits. |
| **5. Add to Cart** | Click *Add to Cart* on candidate games | Updates cart badge and recalculates subtotal and affordability in real time. |
| **6. Purchase Request** | Prompt: *"Buy everything in my cart"* | Purchase Agent validates conditions, creates summary, and pauses LangGraph thread. |
| **7. HITL Approval** | Purchase confirmation modal appears | Shows breakdown (Price, Current Balance, Remaining). Graph waits at approval gate. |
| **8. Approve Purchase** | Click *Approve Purchase* | Atomic MySQL transaction executes: wallet balance decreases, cart clears, game added to library. |
| **9. Verify Persistence** | Open *My Library* tab | Displays purchased games marked `Purchased ✓ / Ready to Play` loaded directly from MySQL. |

---

## 9. Key Architectural Decisions

1. **Why MySQL instead of a Vector DB?**
   - E-commerce inventory, user wallet balances, and game purchases are inherently structured and relational.
   - Financial transactions require strict ACID guarantees (Atomicity, Consistency, Isolation, Durability) to prevent double spending, partial cart checkouts, and race conditions.

2. **Why LangGraph instead of a simple Linear Chain?**
   - GameHub requires stateful multi-agent delegation (Orchestrator ➔ Research ➔ Recommendation) with conditional edges.
   - LangGraph natively supports checkpointing and **Human-in-the-Loop interrupts**, allowing the execution to cleanly pause before destructive operations and resume upon explicit user approval.

3. **Why Specialized Agents?**
   - Single monolithic system prompts become brittle and hallucination-prone. Separating intent classification (Orchestrator), data retrieval (Research), reasoning (Recommendation), and transaction validation (Purchase) keeps each agent explainable, focused, and testable.

4. **Why Controlled Tools?**
   - Directly executing LLM-generated SQL creates severe SQL injection risks and unpredictability. Controlled tool functions encapsulate database operations behind strictly parameterized repository and service layers.
