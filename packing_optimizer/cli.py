"""Command-line interface.

    python -m packing_optimizer examples/items.csv --bags 4 --bag-kg 19 \
           --bag-fee-usd 250 --usd-brl 5.40 --out packing_list.csv
"""

import argparse
import csv
import sys

from .knapsack import fill_bag_greedy
from .models import Item, Plan
from .planner import plan_trip


def brl(value: float) -> str:
    text = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {text}"


def read_items(path: str) -> list[Item]:
    items = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            try:
                items.append(Item(
                    name=row["name"].strip(),
                    weight_kg=float(row["weight_kg"]),
                    profit_brl=float(row["profit_brl"]),
                    quantity=int(row.get("quantity") or 1),
                    must_take=int(row.get("must_take") or 0),
                ))
            except (KeyError, ValueError, TypeError) as err:
                raise ValueError(f"{path}, line {line_no}: {err}") from err
    if not items:
        raise ValueError(f"{path}: no items found")
    return items


def print_plan(plan: Plan) -> None:
    for bag in plan.bags:
        print(f"\nBag {bag.number}: {bag.weight_kg:.2f} / {bag.capacity_kg:g} kg "
              f"({bag.fill_percent:.0f}% full)")
        for name, units in bag.contents.items():
            print(f"   {units:>3} x {name}")
        print(f"   profit {brl(bag.profit_brl)}  -  bag fee {brl(bag.fee_brl)}"
              f"  =  {brl(bag.net_brl)}")

    for bag in plan.skipped_bags:
        print(f"\nBag {bag.number}: NOT worth taking. Best possible profit "
              f"{brl(bag.profit_brl)} is below the {brl(bag.fee_brl)} fee.")

    if plan.unplaced_must_take:
        print("\nWARNING: pre-sold units that did not fit in any bag:")
        for name, units in plan.unplaced_must_take.items():
            print(f"   {units:>3} x {name}")

    if plan.left_behind:
        print("\nLeft behind (no room, or not worth its weight):")
        for name, units in plan.left_behind.items():
            print(f"   {units:>3} x {name}")

    print("\n" + "-" * 60)
    print(f"Bags to take: {len(plan.bags)}    Profit {brl(plan.total_profit_brl)}"
          f"    Fees {brl(plan.total_fees_brl)}")
    print(f"NET PROFIT: {brl(plan.total_net_brl)}")


def save_packing_list(plan: Plan, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["bag", "item", "units"])
        for bag in plan.bags:
            for name, units in bag.contents.items():
                w.writerow([bag.number, name, units])


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="packing_optimizer",
        description="Choose which products go in which suitcase for maximum profit.")
    p.add_argument("items_csv", help="columns: name,weight_kg,profit_brl,quantity,must_take")
    p.add_argument("--bags", type=int, default=4, help="bags available (default 4)")
    p.add_argument("--bag-kg", type=float, default=19.0,
                   help="usable kg per bag after the suitcase's own weight (default 19)")
    p.add_argument("--bag-fee-usd", type=float, default=0.0, help="airline fee per bag")
    p.add_argument("--usd-brl", type=float, default=5.40, help="exchange rate for the fee")
    p.add_argument("--out", help="save a packing list CSV (bag, item, units)")
    p.add_argument("--no-compare", action="store_true",
                   help="skip the comparison against the simple greedy method")
    return p


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        items = read_items(args.items_csv)
        fee_brl = args.bag_fee_usd * args.usd_brl
        plan = plan_trip(items, args.bags, args.bag_kg, fee_brl)
    except (FileNotFoundError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    print_plan(plan)

    if not args.no_compare:
        greedy = plan_trip(items, args.bags, args.bag_kg, fee_brl, fill=fill_bag_greedy)
        gain = plan.total_net_brl - greedy.total_net_brl
        print(f"Simple 'best profit per kg first' packing would net "
              f"{brl(greedy.total_net_brl)}  ->  optimizer gain: {brl(gain)}")

    if args.out:
        save_packing_list(plan, args.out)
        print(f"Saved: {args.out}")
    return 0
