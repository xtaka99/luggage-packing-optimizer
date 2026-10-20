# luggage-packing-optimizer

![tests](https://github.com/xtaka99/luggage-packing-optimizer/actions/workflows/tests.yml/badge.svg)

Decides **which products go in which suitcase** so a buying trip makes the most
money, and tells you when an extra suitcase is not worth its airline fee.

## The problem

My family's import business moves merchandise to Brazil in checked luggage.
Every bag holds about 19 kg of product and costs a fixed airline fee. Demand is
always bigger than the space, so every trip has the same questions:

- With limited kilos, which products earn the most?
- Customers already paid for some items. Those must travel. What fills the rest?
- Is a fourth bag worth paying for, or does it cost more than it earns?

This is the **knapsack problem**, a classic in computer science.

## Why "just take the best profit per kg" is wrong

That greedy rule is what people do by instinct. With a 10 kg limit:

| Item | Weight | Profit | Profit per kg |
|---|---|---|---|
| A | 6 kg | 66 | 11.0 |
| B | 5 kg | 50 | 10.0 |
| C | 5 kg | 50 | 10.0 |

Greedy takes A, then nothing else fits: **66**. The best answer is B + C: **100**.
This tool uses **dynamic programming** to find the true best combination for
each bag, and prints how much it gained over the greedy method.

## Example

```
$ python -m packing_optimizer examples/items.csv --bags 4 --bag-kg 19 \
         --bag-fee-usd 250 --usd-brl 5.40 --out packing_list.csv

Bag 1: 18.98 / 19 kg (100% full)
     3 x Popcorn bucket (seasonal)
     6 x Loungefly mini backpack
     ...
   profit R$ 8.048,00  -  bag fee R$ 1.350,00  =  R$ 6.698,00
...
Bag 4: NOT worth taking. Best possible profit R$ 400,00 is below the R$ 1.350,00 fee.

Left behind (no room, or not worth its weight):
     1 x Coffee mug
     3 x Hardcover art book

Bags to take: 3    Profit R$ 16.680,00    Fees R$ 4.050,00
NET PROFIT: R$ 12.630,00
Simple 'best profit per kg first' packing would net R$ 12.550,00  ->  optimizer gain: R$ 80,00
```

The gain over greedy depends on the mix. With many small, light items (like
this example) greedy is already close. With fewer, heavier items the gap grows
quickly, as in the A/B/C case above. The "skip bag 4" call alone avoided paying
R$ 1.350 to carry R$ 400 of profit.

Example data is fictional.

## Input

A CSV with one row per product:

```
name,weight_kg,profit_brl,quantity,must_take
Spirit jersey,0.48,160,12,4
```

- `profit_brl`: profit per unit **before** baggage cost (the bag fee is charged per bag by the tool)
- `quantity`: units available or in demand
- `must_take`: units already sold. These are packed first, no matter what

## Setup

Python 3.10+. No dependencies.

```bash
git clone https://github.com/xtaka99/luggage-packing-optimizer.git
cd luggage-packing-optimizer
python -m packing_optimizer examples/items.csv --bags 4 --bag-fee-usd 250
```

Tests:

```bash
pip install -r requirements-dev.txt
pytest
```

## How it works

| File | Job |
|---|---|
| `packing_optimizer/models.py` | `Item`, `Bag`, `Plan` dataclasses with validation |
| `packing_optimizer/knapsack.py` | Single-bag solvers: dynamic programming (optimal) and greedy (baseline). The docstring explains the algorithm step by step |
| `packing_optimizer/planner.py` | Multi-bag plan: pre-sold items first, then fill each bag, skip bags that lose money |
| `packing_optimizer/cli.py` | `argparse` interface, report, packing-list CSV |
| `tests/` | 20 tests, including a **brute-force check**: on 40 random small cases the DP result must equal the best of every possible combination |

Details worth knowing:

- **Weights become whole numbers.** DP needs integers, so weights are converted to 10 g steps and rounded **up**, which guarantees a bag can never come out overweight.
- **Bounded quantities use binary splitting.** 12 identical units become bundles of 1, 2, 4 and 5, which can form any count from 0 to 12 with 4 entries instead of 12.
- **Complexity** is O(bundles x capacity steps): around 100 x 1,900 operations per bag, which runs instantly.
- **Limit:** packing several bags at once is the *multiple knapsack problem*, which has no fast exact solution. Filling bags one after another with an optimal single-bag solver is a standard approximation, not a proof of the global optimum. It also ignores volume and fragility; weight is the constraint airlines enforce.

## What I learned

- Dynamic programming: building a table of sub-answers and reconstructing the decisions
- Why greedy algorithms fail on knapsack, and how to show it with a counter-example
- Verifying an algorithm against brute force with seeded random tests
- Being precise about what is optimal and what is an approximation

## Next steps

- Read weights and profits straight from [landed-cost-calculator](https://github.com/xtaka99/landed-cost-calculator) output
- Read `must_take` counts from [whatsapp-order-parser](https://github.com/xtaka99/whatsapp-order-parser) buy lists
- Add a volume limit per bag

## License

MIT
