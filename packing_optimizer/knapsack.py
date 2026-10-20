"""Two ways to fill ONE bag. This file is the algorithmic heart of the project.

THE PROBLEM (the classic "knapsack problem")
    A bag holds a limited weight. Each item has a weight and a profit.
    Which combination of items gives the most profit without going over?

WHY THE OBVIOUS ANSWER IS WRONG
    The obvious method is greedy: sort by profit per kg and keep adding the
    best one that still fits. It is fast but can be badly wrong. Example with
    a 10 kg bag:
        A: 6 kg, profit 66  (11.0 per kg)   <- greedy takes this first
        B: 5 kg, profit 50  (10.0 per kg)
        C: 5 kg, profit 50  (10.0 per kg)
    Greedy packs A (66) and then nothing else fits. The best answer is B + C
    (100). Greedy left a third of the profit on the table.

THE BETTER METHOD: DYNAMIC PROGRAMMING (DP)
    Build a table best[w] = "the most profit possible with a weight limit of
    w". Start with every entry at 0, then consider the items one at a time.
    For each item and each w:

        best[w] = max( best[w],                               # skip the item
                       best[w - item_weight] + item_profit )  # take the item

    Every small answer is reused to build bigger ones, so after the last item
    best[capacity] is guaranteed optimal. A second table, `took`, remembers
    each decision so the chosen items can be read back at the end.

    DP needs whole-number weights, so weights are converted to 10 g steps
    (a 19 kg bag = 1,900 steps). Work grows with (number of items x steps),
    which is tiny for a computer at this size.

QUANTITIES
    "12 units of the same keychain" could be treated as 12 separate items, but
    that is wasteful. Binary splitting turns 12 into bundles of 1, 2, 4 and 5:
    any amount from 0 to 12 can be made by combining those four bundles, so
    the DP handles 4 entries instead of 12.
"""

from .models import GRAMS_PER_STEP, Item


def capacity_steps(capacity_kg: float) -> int:
    """Bag capacity in 10 g steps, rounded DOWN (the safe direction)."""
    return int(round(capacity_kg * 1000)) // GRAMS_PER_STEP


def split_into_bundles(items: list[Item], available: dict[str, int]):
    """Binary splitting. Returns a list of (item, units_in_bundle)."""
    bundles = []
    for item in items:
        remaining = available.get(item.name, 0)
        size = 1
        while remaining > 0:
            take = min(size, remaining)
            bundles.append((item, take))
            remaining -= take
            size *= 2
    return bundles


def fill_bag_dp(items: list[Item], available: dict[str, int],
                capacity_kg: float) -> dict[str, int]:
    """Optimal contents for one bag. Returns {item name: units}."""
    capacity = capacity_steps(capacity_kg)
    bundles = [b for b in split_into_bundles(items, available)
               if b[0].profit_brl > 0 and b[0].steps * b[1] <= capacity]
    if capacity <= 0 or not bundles:
        return {}

    best = [0.0] * (capacity + 1)
    took = [[False] * (capacity + 1) for _ in bundles]

    for i, (item, units) in enumerate(bundles):
        weight = item.steps * units
        profit = item.profit_brl * units
        # Walk w from high to low so each bundle is used at most once.
        for w in range(capacity, weight - 1, -1):
            candidate = best[w - weight] + profit
            if candidate > best[w]:
                best[w] = candidate
                took[i][w] = True

    # Read the decisions backwards to recover what was packed.
    chosen: dict[str, int] = {}
    w = capacity
    for i in range(len(bundles) - 1, -1, -1):
        if took[i][w]:
            item, units = bundles[i]
            chosen[item.name] = chosen.get(item.name, 0) + units
            w -= item.steps * units
    return chosen


def fill_bag_greedy(items: list[Item], available: dict[str, int],
                    capacity_kg: float) -> dict[str, int]:
    """Baseline for comparison: best profit-per-kg first, one unit at a time."""
    remaining = capacity_steps(capacity_kg)
    chosen: dict[str, int] = {}
    for item in sorted(items, key=lambda i: i.profit_per_kg, reverse=True):
        if item.profit_brl <= 0:
            continue
        units = min(available.get(item.name, 0), remaining // item.steps)
        if units > 0:
            chosen[item.name] = units
            remaining -= item.steps * units
    return chosen
