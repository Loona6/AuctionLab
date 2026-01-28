
# 🧪 Auction Lab – Auction Simulation Game

Auction Lab is an interactive simulation game that models real-world auction dynamics using AI-driven bidding strategies. Players compete against AI agents, analyse strategies, and optimize bidding decisions to maximize profit.

This project combines **game mechanics, AI behaviour modelling, and statistical analysis** to create a realistic auction environment for learning and experimentation.

---

## 🎯 Project Objectives

- Simulate real-world auction scenarios.
- Implement AI bidders with different strategies.
- Allow players to test bidding strategies.
- Track performance metrics and strategy effectiveness.
- Visualize trends in decision-making and outcomes.

---

## 🎮 Gameplay Overview (Player Perspective)

### 1️⃣ Start Game & Budget Allocation

- Player starts with a fixed budget (e.g., 500 coins).
- Initial stats are displayed:
    - Current budget
    - High score
    - Past performance

---

### 2️⃣ Item Appearance

- An item appears for auction.
- The **true value** of the item is hidden.
- Players receive partial hints (visual or textual).

---

### 3️⃣ Round Begins

- Each round is time-limited.
- Player observes:
    - AI bidders
    - Real-time bids

---

### 4️⃣ AI Behavior

AI agents follow probabilistic bidding strategies:
- **Aggressive AI** → bids high
- **Conservative AI** → bids low to mid-range
- **Random AI** → unpredictable behavior

---

### 5️⃣ Player Bidding

- Player places a bid within their budget.
- Player can:
    - Increase bid
    - Retract bid (before round ends)

---

### 6️⃣ Round Outcome

- Highest bid wins the item.
- Profit/Loss calculation:
    `Profit/Loss = True Value − Bid Price
- Player budget updates.
- Session stats update:
    - Items won
    - Profit/Loss
    - Strategy performance

---

### 7️⃣ Multiple Rounds

- Game continues for multiple rounds (e.g., 5 rounds).
- Player adapts strategy based on:
    - Past results
    - AI behavior patterns


---

### 8️⃣ Game End

Game ends when:

- Player runs out of budget, OR
- All rounds are completed

Final results display:

- Total profit / high score
- Items won
- Strategy success rates
- Performance trends

---

## ⚡ Random Events During Rounds

To increase realism, random events may occur:

- AI bid retractions
- Last-second bid snipes
- Sudden competition spikes (AI increases bids probabilistically)

---

## 🧠 Strategy System

### Player Strategies

- **Aggressive** → Bid near maximum
- **Conservative** → Bid low to mid-range
- **Random** → Bid unpredictably

### Strategy Success Rate

For each strategy:

- Track number of wins
- Compute success rate:

`Success Rate (%) = (Wins using strategy / Total rounds using strategy) × 100`

---

## 📊 Statistics & Analytics

### Per Round

- Player bid
- Winning bid
- Profit/Loss
- Strategy used

### Per Session

- Total profit
- Items won
- Average bid vs winning bid
- Strategy success rates

### Across All Games

- Highest score
- Cumulative strategy success rates
- Long-term trends in strategy effectiveness


---

## 💎 Item Value Estimation

Each item has a hidden true value.
AI estimates value using randomness:
`Estimated Value = True Value + Random Noise`
Where random noise is ±10% to ±30% of the true value.

---

## 🤖 AI Bidding Strategies

### 🔥 Aggressive AI

Bids close to or above estimated value:

`Bid = Estimated Value × (1 + r) r ∈ [0.05, 0.25]`

### 🛡️ Conservative AI

Bids below or near estimated value:
`Bid = Estimated Value × (1 − r) r ∈ [0.05, 0.20]`


### 🎲 Random AI

Bids unpredictably within budget:
`Bid = Random amount within budget`
Simulates irrational or chaotic bidders.