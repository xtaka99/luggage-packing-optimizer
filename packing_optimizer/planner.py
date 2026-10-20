"""Plans a whole trip: several bags, pre-sold items, and "is this bag worth it?".

Steps:
    1. Pre-sold (must_take) units go in first, heaviest first, each into the
       first bag with room. They travel no matter what, because a customer
       already paid.
    2. Each bag's remaining space is filled with the single-bag method from
       knapsack.py, one bag after another, removing what was packed.
    3. A bag with no pre-sold items is only taken if its profit beats the
       airline's fee for it. Bags are filled best-first, so once one bag is
       not worth it, no later bag will be either.

Honest note: packing several bags at once is a harder problem ("multiple
knapsack") with no fast perfect solution. Filling bags one after another with
an optimal single-bag method is a standard, strong approximation, and the
tests compare it against a brute-force search on small cases.
"""

from collections.abc import Callable

from .knapsack import fill_bag_dp
from .models import Bag, Item, Plan

FillMethod = Callable[[list[Item], dict[str, int], float], dict[str, int]]


def plan_trip(items: list[Item], bag_count: int, bag_kg: float,
              bag_fee_brl: float = 0.0, fill: FillMethod = fill_bag_dp) -> Plan:
    if bag_count < 1:
        raise ValueError("bag_count must be at least 1")
    if bag_kg <= 0:
        raise ValueError("bag_kg must be greater than zero")
    names = [i.name for i in items]
    if len(names) != len(set(names)):
        raise ValueError("Item names must be unique")

    by_name = {i.name: i for i in items}
    bags = [Bag(n + 1, bag_kg, bag_fee_brl) for n in range(bag_count)]
    available = {i.name: i.quantity for i in items}
    unplaced: dict[str, int] = {}

    # ---- 1. pre-sold units first (first-fit, heaviest first) ----
    for item in sorted(items, key=lambda i: i.weight_kg, reverse=True):
        for _ in range(item.must_take):
            home = next((b for b in bags
                         if b.weight_kg + item.weight_kg <= b.capacity_kg + 1e-9), None)
            if home is None:
                unplaced[item.name] = unplaced.get(item.name, 0) + 1
            else:
                home.add(item, 1)
                home.has_must_take = True
            available[item.name] -= 1

    # ---- 2 and 3. fill remaining space, bag by bag ----
    taken, skipped = [], []
    for bag in bags:
        free_kg = round(bag.capacity_kg - bag.weight_kg, 3)
        chosen = fill(items, available, free_kg)
        extra_profit = sum(by_name[n].profit_brl * u for n, u in chosen.items())

        worth_it = bag.has_must_take or (bag.profit_brl + extra_profit) > bag.fee_brl
        if not worth_it:
            for name, units in chosen.items():       # show what it WOULD have held
                bag.add(by_name[name], units)
            skipped.append(bag)
            continue

        for name, units in chosen.items():
            bag.add(by_name[name], units)
            available[name] -= units
        taken.append(bag)

    left = {name: units for name, units in available.items() if units > 0}
    return Plan(taken, skipped, left, unplaced)
