from collections import Counter
from collections.abc import MutableMapping, MutableSet
from typing import Any
from weakref import WeakSet


class AbstractStatistic:
    __metrics__: frozenset[str]
    __instances__: MutableSet["AbstractStatistic"]
    _counter: MutableMapping[str, float | int]
    name: str | None


CLASS_STORE: set[type[AbstractStatistic]] = set()


class Metric:
    __slots__ = ("name", "counter")

    def __init__(
        self,
        name: str,
        counter: MutableMapping[str, float | int],
        default: float | int = 0,
    ):
        self.name: str = name
        self.counter = counter
        self.counter[name] = default

    def __get__(self, _instance: Any, _owner: type[Any]) -> float | int:
        return self.counter[self.name]

    def __set__(self, _instance: Any, value: float | int) -> None:
        self.counter[self.name] = value

    def __iadd__(self, value: float | int) -> "Metric":
        self.counter[self.name] += value
        return self

    def __isub__(self, value: float | int) -> "Metric":
        self.counter[self.name] -= value
        return self

    def __eq__(self, other: Any) -> bool:
        return self.counter[self.name] == other

    def __hash__(self) -> int:
        return hash(self.counter[self.name])


class MetaStatistic(type):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        dct: dict[str, Any],
    ) -> Any:
        # noinspection PyTypeChecker
        klass: type[AbstractStatistic] = super().__new__(  # type: ignore
            mcs,
            name,
            bases,
            dct,
        )

        metrics = set()

        for base_class in bases:
            if not issubclass(base_class, AbstractStatistic):
                continue

            if not hasattr(base_class, "__annotations__"):
                continue

            for prop, kind in base_class.__annotations__.items():
                if kind not in (int, float):
                    continue

                if prop.startswith("_"):
                    continue

                metrics.add(prop)

        for prop, kind in klass.__annotations__.items():
            if kind not in (int, float):
                continue

            metrics.add(prop)

        klass.__metrics__ = frozenset(metrics)

        if klass.__metrics__:
            klass.__instances__ = WeakSet()
            CLASS_STORE.add(klass)

        return klass


class Statistic(AbstractStatistic, metaclass=MetaStatistic):
    __slots__ = ("_counter", "name")

    def __init__(self, name: str | None = None) -> None:
        self._counter = Counter()  # type: ignore
        self.name = name

        for prop in self.__metrics__:
            setattr(self, prop, Metric(prop, self._counter))

        self.__instances__.add(self)
