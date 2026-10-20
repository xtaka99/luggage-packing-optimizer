"""Data containers used by every other file."""

from dataclasses import dataclass, field

GRAMS_PER_STEP = 10      # weights are handled in 10 g steps (see knapsack.py)


@dataclass(frozen=True)
class Item:
    """A product that could be packed.

    profit_brl: profit for ONE unit, freight not included (the bag fee is
                charged per bag by the planner, so it must not be counted twice).
    quantity:   how many units are available / in demand.
    must_take:  how many of those units are already sold and MUST travel.
    """

    name: str
    weight_kg: float
    profit_brl: float
    quantity: int = 1
    must_take: int = 0

    def __post_init__(self) -> None:
        if self.weight_kg <= 0:
            raise ValueError(f"{self.name}: weight must be greater than zero")
        if self.quantity < 1:
            raise ValueError(f"{self.name}: quantity must be at least 1")
        if not 0 <= self.must_take <= self.quantity:
            raise ValueError(f"{self.name}: must_take must be between 0 and quantity")

    @property
    def steps(self) -> int:
        """Weight in 10 g steps, rounded UP so a bag can never end up overweight."""
        grams = round(self.weight_kg * 1000)
        return -(-grams // GRAMS_PER_STEP)          # ceiling division

    @property
    def profit_per_kg(self) -> float:
        return self.profit_brl / self.weight_kg


@dataclass
class Bag:
    number: int
    capacity_kg: float
    fee_brl: float
    contents: dict[str, int] = field(default_factory=dict)    # item name -> units
    weight_kg: float = 0.0
    profit_brl: float = 0.0
    has_must_take: bool = False

    @property
    def net_brl(self) -> float:
        """Profit after paying the airline for this bag."""
        return self.profit_brl - self.fee_brl

    @property
    def fill_percent(self) -> float:
        return self.weight_kg / self.capacity_kg * 100 if self.capacity_kg else 0.0

    def add(self, item: Item, units: int) -> None:
        self.contents[item.name] = self.contents.get(item.name, 0) + units
        self.weight_kg = round(self.weight_kg + item.weight_kg * units, 3)
        self.profit_brl = round(self.profit_brl + item.profit_brl * units, 2)


@dataclass
class Plan:
    bags: list[Bag]                       # bags worth taking, in order
    skipped_bags: list[Bag]               # bags that would lose money
    left_behind: dict[str, int]           # item name -> units not packed
    unplaced_must_take: dict[str, int]    # pre-sold units that did not fit anywhere

    @property
    def total_profit_brl(self) -> float:
        return round(sum(b.profit_brl for b in self.bags), 2)

    @property
    def total_fees_brl(self) -> float:
        return round(sum(b.fee_brl for b in self.bags), 2)

    @property
    def total_net_brl(self) -> float:
        return round(self.total_profit_brl - self.total_fees_brl, 2)
