from typing import Any, TypeAlias, Union

NaiveRange: TypeAlias = tuple[int, int]


class RangeError(Exception):
    pass


class AttnRange:
    """A dataclass to manage any indices range like [start, end) for attention computation"""

    def __init__(self, start: int, end: int) -> None:
        self.check_valid(start=start, end=end)

        self._start = start
        self._end = end

    @property
    def start(self) -> int:
        return self._start

    @start.setter
    def start(self, value) -> None:
        self.check_valid(start=value)
        self._start = value

    @property
    def end(self) -> int:
        return self._end

    @end.setter
    def end(self, value) -> None:
        self.check_valid(end=value)
        self._end = value

    @property
    def size(self) -> int:
        return self._end - self._start

    @property
    def seqlen(self) -> int:
        return self.size

    def to_naive_range(self) -> NaiveRange:
        return (self._start, self._end)

    @staticmethod
    def from_range(
        attn_range: Union[NaiveRange, "AttnRange"],
        check: bool = True,
    ) -> "AttnRange":
        if isinstance(attn_range, AttnRange):  # just copy
            res = attn_range
        else:
            res = AttnRange(start=attn_range[0], end=attn_range[1])

        if check:
            res.check_valid()

        return res

    def offset(self, offset: int) -> "AttnRange":
        return AttnRange(start=self._start + offset, end=self._end + offset)

    def intersect(self, other: "AttnRange") -> "AttnRange":
        start = max(self._start, other._start)
        end = min(self._end, other._end)

        return AttnRange(start=min(start, end), end=end)

    def diff_by(self, other: "AttnRange") -> list["AttnRange"]:
        """other - self"""
        diff_ranges = []

        inter_range = self.intersect(other)

        if inter_range == self:  # self is a subrange of other
            diff_ranges.append(AttnRange(other.start, self.start))
            diff_ranges.append(AttnRange(self.end, other.end))
        elif inter_range == other:  # k_range is a subrange of q_range
            diff_ranges.append(AttnRange(other.start, other.start))
        elif inter_range.is_empty():  # q_range and k_range are disjoint
            diff_ranges.append(AttnRange.from_range(other))
        else:  # q_range and k_range are overlapping, but neither of them cover the other
            if other.start < self.start:
                diff_ranges.append(AttnRange(other.start, self.start))
            else:
                diff_ranges.append(AttnRange(self.end, other.end))

        diff_ranges = [
            diff_range for diff_range in diff_ranges if not diff_range.is_empty()
        ]

        return diff_ranges

    def is_subrange_of(self, other: "AttnRange") -> bool:
        return self._start >= other._start and self._end <= other._end

    def is_empty(self) -> bool:
        return self._start == self._end

    def is_valid(self, start: int | None = None, end: int | None = None) -> bool:
        start = self._start if start is None else start
        end = self._end if end is None else end

        return 0 <= start <= end

    def check_valid(self, start: int | None = None, end: int | None = None) -> None:
        if not self.is_valid(start, end):
            raise RangeError(
                f"The attn_range {(start, end)} is invalid against the rule: '0 <= start <= end'"
            )

    def __len__(self) -> int:
        return self.size

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, AttnRange):
            return self._start == other._start and self._end == other._end
        return False

    def __repr__(self) -> str:
        return f"[{self._start}, {self._end})"


RangeType: TypeAlias = AttnRange | NaiveRange
