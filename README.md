# CharmCost

A calculator that compares material cost and suggested retail pricing for charm jewelry across metal options — 18k gold, 14k gold, 10k gold, sterling silver, and fine silver — using **live** gold and silver spot prices.

## The problem this solves

Someone launching a charm jewelry line has to pick a metal (or metals) before they can price anything, and that decision has huge cost implications that shift daily with the market. Doing this math by hand — spot price → per-gram purity price → material cost → margin-adjusted retail price — for every metal option, every time gold moves, is slow and error-prone.

CharmCost takes a charm's weight, a labor/overhead estimate, and a target profit margin, and instantly shows the material cost and suggested price for each metal side by side, using the current spot market.

**User needs this addresses:**
- *A jewelry business owner needs to compare 18k, 14k, and sterling silver costs for the same charm design so they can decide which metal(s) to launch with.*
- *A jewelry business owner needs to see how their margin holds up across metals at today's prices so they can set retail pricing with confidence.*

**Data source:** [xaus.com](https://xaus.com) — a free, keyless, continuously-updated spot price API for gold and silver.

## What it is not

Spot price is the raw commodity market price, not a fabricated/retail bullion price — it doesn't include casting, alloying, or dealer premiums beyond what you enter as "labor/overhead." This tool is meant to support a pricing decision, not to be a definitive cost accounting system.

---

## Project structure

```
charmcost/
├── app.py                      # Flask web app (main user-facing interface)
├── charmcost/
│   ├── __init__.py
│   ├── spot_price_client.py    # Thin HTTP client for the spot price API (with short-TTL cache)
│   ├── calculator.py           # Business logic: metal comparison & margin pricing
│   └── cli.py                  # Command-line interface (alternative to the web app)
├── templates/
│   └── index.html              # Web UI template
├── tests/
│   ├── test_spot_price_client.py
│   ├── test_calculator.py
│   └── test_app.py
├── .github/workflows/ci.yml    # GitHub Actions: runs pytest on every push/PR
├── requirements.txt
├── .env.example
├── .gitignore
└── LICENSE.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/charmcost.git
cd charmcost
```

### 2. Create and activate a virtual environment (via Anaconda)

```bash
conda create -n charmcost python=3.12
conda activate charmcost
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

No API key is required — the spot price API is free and keyless. `.env` only controls local Flask server settings. **Do not commit your `.env` file** — it's already excluded via `.gitignore`.

---

## Running the program

### Option A: Web app (recommended)

```bash
python app.py
```

Then open **http://localhost:5000**. Enter a charm weight, labor cost, and target margin, pick which metals to compare, and submit.

### Option B: Command line

```bash
python -m charmcost.cli --weight 3.0 --labor 8.00 --margin 50
python -m charmcost.cli --weight 2.5 --labor 6.00 --margin 60 --metals 18k_gold 14k_gold fine_silver
```

---

## Running tests

Tests use `pytest` and mock all network calls, so they run fully offline and won't fail due to live market volatility or external API downtime.

```bash
pytest -v
```

Continuous integration via **GitHub Actions** runs this same test suite automatically on every push and pull request (see `.github/workflows/ci.yml`).

---

## How it works (high level)

1. User submits a charm weight, labor cost, target margin, and metal selection via the web form or CLI.
2. `spot_price_client.py` fetches live gold (per gram, 24k) and silver (per troy oz, converted to per gram) prices from `xaus.com`, caching the result for 60 seconds to avoid hammering the API.
3. `calculator.py` applies standard karat/fineness purity fractions (18k = 75%, 14k = 58.3%, 10k = 41.7%, sterling = 92.5%, fine silver = 99.9%) to get a per-gram cost for each metal, multiplies by charm weight for material cost, adds labor cost, and applies the margin formula `price = total_cost / (1 - margin%)` to get a suggested retail price.
4. Results are sorted most-to-least expensive and rendered in the web UI or printed to the terminal.

## Known limitations / next steps

- Spot price is a live commodity market rate; it doesn't include a bullion dealer's fabrication premium, which real-world sourcing (a refiner or findings supplier) would add on top.
- Currently compares single charms one at a time; a natural next feature is a full "charm bracelet" mode that sums several charms with different weights/metals into one order total.
- The margin formula assumes a flat labor/overhead number per charm; a more advanced version could break that into casting, polishing, and findings line items.

## License

MIT — see [LICENSE.md](LICENSE.md).
