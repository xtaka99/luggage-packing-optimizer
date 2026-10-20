"""Tests for the single-bag algorithms, including a brute-force proof check."""

import itertools
import random

import pytest

from packing_optimizer.knapsack import (capacity_steps, fill_bag_dp, fill_bag_greedy,
                                        split_into_bundles)
from packing_optimizer.models import Item


def profit_of(chosen, items):
    by_name = {i.name: i for i in items}
    return sum(by_name[n].profit_brl * u for n, u in chosen.items())


def weight_of(chosen, items):
    by_name = {i.name: i for i in items}
    return sum(by_name[n].weight_kg * u for n, u in chosen.items())


def brute_force_best(items, capacity_kg):
    """Try EVERY combination. Only feasible for tiny inputs, but always right."""
    best = 0.0
    ranges = [range(i.quantity + 1) for i in items]
    for combo in itertools.product(*ranges):
        steps = sum(i.steps * u for i, u in zip(items, combo))
        if steps <= capacity_steps(capacity_kg):
            best = max(best, sum(i.profit_brl * u for i, u in zip(items, combo)))
    return best


# The example from the knapsack.py docstring.
A = Item("A", 6, 66)
B = Item("B", 5, 50)
C = Item("C", 5, 50)


def test_dp_beats_greedy_on_the_classic_trap():
    items, available = [A, B, C], {"A": 1, "B": 1, "C": 1}
    assert profit_of(fill_bag_greedy(items, available, 10), items) == 66
    assert fill_bag_dp(items, available, 10) == {"B": 1, "C": 1}


def test_dp_matches_brute_force_on_random_cases():
    rng = random.Random(42)                  # fixed seed = same cases every run
    for _ in range(40):
        items = [Item(f"item{n}", rng.randint(5, 60) / 10, rng.randint(10, 300),
                      quantity=rng.randint(1, 3)) for n in range(5)]
        available = {i.name: i.quantity for i in items}
        capacity = rng.randint(30, 120) / 10
        chosen = fill_bag_dp(items, available, capacity)
        assert profit_of(chosen, items) == pytest.approx(brute_force_best(items, capacity))


def test_dp_never_exceeds_capacity_or_stock():
    items = [Item("mug", 0.52, 70, 14), Item("pin", 0.12, 48, 25), Item("book", 1.85, 110, 3)]
    available = {i.name: i.quantity for i in items}
    chosen = fill_bag_dp(items, available, 19)
    assert weight_of(chosen, items) <= 19
    for name, units in chosen.items():
        assert units <= available[name]


def test_weights_round_up_to_stay_safe():
    assert Item("x", 0.123, 1).steps == 13      # 123 g -> 13 steps of 10 g, not 12


def test_binary_splitting_covers_every_quantity():
    item = Item("k", 1, 1, quantity=12)
    sizes = [units for _, units in split_into_bundles([item], {"k": 12})]
    assert sizes == [1, 2, 4, 5]
    reachable = {sum(c) for r in range(5) for c in itertools.combinations(sizes, r)}
    assert reachable == set(range(13))


def test_items_with_no_profit_are_never_packed():
    items = [Item("loss", 1, -5), Item("zero", 1, 0), Item("good", 1, 10)]
    available = {"loss": 1, "zero": 1, "good": 1}
    assert fill_bag_dp(items, available, 10) == {"good": 1}
    assert fill_bag_greedy(items, available, 10) == {"good": 1}


def test_empty_or_tiny_bag_returns_nothing():
    assert fill_bag_dp([A], {"A": 1}, 0) == {}
    assert fill_bag_dp([A], {"A": 1}, 5.99) == {}
