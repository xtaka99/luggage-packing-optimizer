import pytest

from packing_optimizer.cli import brl, run
from packing_optimizer.knapsack import fill_bag_greedy
from packing_optimizer.models import Item
from packing_optimizer.planner import plan_trip


def test_items_are_never_packed_twice_across_bags():
    items = [Item("plush", 1, 100, quantity=5)]
    plan = plan_trip(items, bag_count=3, bag_kg=2)
    assert sum(b.contents.get("plush", 0) for b in plan.bags) == 5
    assert plan.left_behind == {}


def test_bag_that_cannot_cover_its_fee_is_skipped():
    items = [Item("plush", 1, 100, quantity=3)]
    plan = plan_trip(items, bag_count=2, bag_kg=2, bag_fee_brl=150)
    assert len(plan.bags) == 1                  # bag 1: 200 profit > 150 fee
    assert len(plan.skipped_bags) == 1          # bag 2: 100 profit < 150 fee
    assert plan.left_behind == {"plush": 1}
    assert plan.total_net_brl == 50


def test_presold_units_travel_even_when_unprofitable():
    items = [Item("presold", 1, 10, quantity=1, must_take=1)]
    plan = plan_trip(items, bag_count=1, bag_kg=5, bag_fee_brl=500)
    assert plan.bags[0].contents == {"presold": 1}
    assert plan.total_net_brl == -490           # honest: this trip loses money


def test_presold_units_get_priority_over_better_items():
    items = [Item("presold", 3, 10, quantity=1, must_take=1),
             Item("star", 3, 500, quantity=2)]
    plan = plan_trip(items, bag_count=1, bag_kg=6)
    assert plan.bags[0].contents == {"presold": 1, "star": 1}
    assert plan.left_behind == {"star": 1}


def test_presold_unit_too_big_for_any_bag_is_reported():
    items = [Item("statue", 25, 900, quantity=1, must_take=1)]
    plan = plan_trip(items, bag_count=2, bag_kg=19)
    assert plan.unplaced_must_take == {"statue": 1}


def test_optimizer_is_never_worse_than_greedy_on_the_example():
    from packing_optimizer.cli import read_items
    items = read_items("examples/items.csv")
    smart = plan_trip(items, 4, 19, 1350)
    simple = plan_trip(items, 4, 19, 1350, fill=fill_bag_greedy)
    assert smart.total_net_brl >= simple.total_net_brl
    for bag in smart.bags:
        assert bag.weight_kg <= bag.capacity_kg


@pytest.mark.parametrize("kwargs", [
    dict(name="x", weight_kg=0, profit_brl=1),
    dict(name="x", weight_kg=1, profit_brl=1, quantity=0),
    dict(name="x", weight_kg=1, profit_brl=1, quantity=2, must_take=3),
])
def test_invalid_items_are_rejected(kwargs):
    with pytest.raises(ValueError):
        Item(**kwargs)


def test_duplicate_names_and_bad_settings_are_rejected():
    with pytest.raises(ValueError):
        plan_trip([Item("a", 1, 1), Item("a", 2, 2)], 1, 19)
    with pytest.raises(ValueError):
        plan_trip([Item("a", 1, 1)], 0, 19)


def test_cli_runs_and_saves_packing_list(tmp_path, capsys):
    out = tmp_path / "list.csv"
    code = run(["examples/items.csv", "--bags", "4", "--bag-fee-usd", "250",
                "--out", str(out)])
    text = capsys.readouterr().out
    assert code == 0
    assert "NET PROFIT" in text and "optimizer gain" in text
    assert out.read_text(encoding="utf-8-sig").splitlines()[0] == "bag,item,units"


def test_cli_reports_bad_csv(tmp_path, capsys):
    bad = tmp_path / "bad.csv"
    bad.write_text("name,weight_kg,profit_brl\nmug,heavy,10\n")
    assert run([str(bad)]) == 1
    assert "line 2" in capsys.readouterr().err


def test_brl_format():
    assert brl(12630) == "R$ 12.630,00"
