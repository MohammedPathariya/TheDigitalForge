"""Evaluator-only cases.

This module must never be imported by a model-facing prompt builder. Cases are tuples of
frozen records so an in-process caller cannot mutate the canonical evaluator data.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class HiddenCase:
    args: tuple[Any, ...]
    expected: Any


_RAW_CASES = {
    "forge_easy_01": (
        HiddenCase(([4, 1, 4],), 1),
        HiddenCase(([9],), 9),
        HiddenCase(([-2, 7, 7, -2, 0],), 0),
        HiddenCase(([3, 5, 3, 8, 8],), 5),
    ),
    "forge_easy_02": (
        HiddenCase(([],), []),
        HiddenCase((["a", "b", "a", "c", "b"],), ["a", "b", "c"]),
        HiddenCase((["A", "a", "A"],), ["A", "a"]),
        HiddenCase((["same", "same"],), ["same"]),
    ),
    "forge_easy_03": (
        HiddenCase(([], ["a"]), []),
        HiddenCase((["iron", "wood", "iron"], ["wood", "glass"]), ["wood"]),
        HiddenCase((["z", "a", "M"], ["a", "z", "M", "z"]), ["M", "a", "z"]),
        HiddenCase((["Tag"], ["tag"]), []),
    ),
    "forge_easy_04": (
        HiddenCase(("",), True),
        HiddenCase(("draft({a[0]})",), True),
        HiddenCase(("([)]",), False),
        HiddenCase(("text }",), False),
        HiddenCase(("no brackets",), True),
    ),
    "forge_easy_05": (
        HiddenCase(([], 12), []),
        HiddenCase(([1, 2, 3, 4], 1), [4, 1, 2, 3]),
        HiddenCase(([1, 2, 3, 4], 6), [3, 4, 1, 2]),
        HiddenCase(([7], 99), [7]),
        HiddenCase(([0, -1, 5], 0), [0, -1, 5]),
    ),
    "forge_easy_06": (
        HiddenCase(([],), []),
        HiddenCase(([3, 1, 4, 4, 2],), [3, 3, 4, 4, 4]),
        HiddenCase(([-5, -8, -2],), [-5, -5, -2]),
        HiddenCase(([9],), [9]),
    ),
    "forge_easy_07": (
        HiddenCase(([], 3), 0),
        HiddenCase(([1, 3, 3, 7], 3), 1),
        HiddenCase(([1, 3, 3, 7], 4), 3),
        HiddenCase(([-4, 0, 9], -10), 0),
        HiddenCase(([2, 2, 2], 2), 0),
    ),
    "forge_easy_08": (
        HiddenCase(([],), True),
        HiddenCase(([1],), True),
        HiddenCase(([1, 2, 2, 8],), True),
        HiddenCase(([8, 8, 2, -1],), True),
        HiddenCase(([1, 3, 2],), False),
    ),
    "forge_easy_09": (
        HiddenCase(("",), True),
        HiddenCase(("Forge, egrof!",), True),
        HiddenCase(("A man, a plan, 2 canals: 2, nalp a nam A",), False),
        HiddenCase(("éaé",), True),
        HiddenCase(("0P",), False),
    ),
    "forge_easy_10": (
        HiddenCase(([],), 0),
        HiddenCase(([5],), 0),
        HiddenCase(([7, 1, 5, 3, 6, 4],), 5),
        HiddenCase(([7, 6, 4, 3, 1],), 0),
        HiddenCase(([2, 2, 8],), 6),
    ),
    "forge_medium_01": (
        HiddenCase(([],), []),
        HiddenCase(([[5, 8], [1, 3], [3, 4]],), [[1, 4], [5, 8]]),
        HiddenCase(([[1, 10], [2, 3], [10, 12]],), [[1, 12]]),
        HiddenCase(([[0, 0], [2, 2]],), [[0, 0], [2, 2]]),
    ),
    "forge_medium_02": (
        HiddenCase(([],), 0),
        HiddenCase(([[0, 10], [10, 20]],), 1),
        HiddenCase(([[0, 30], [5, 10], [15, 20]],), 2),
        HiddenCase(([[1, 4], [2, 5], [3, 6], [6, 8]],), 3),
    ),
    "forge_medium_03": (
        HiddenCase(([],), []),
        HiddenCase(([[1, 2, 3]],), [1, 2, 3]),
        HiddenCase(([[1], [2], [3]],), [1, 2, 3]),
        HiddenCase(([[1, 2, 3], [4, 5, 6]],), [1, 2, 3, 6, 5, 4]),
        HiddenCase(([[1, 2, 3], [4, 5, 6], [7, 8, 9]],), [1, 2, 3, 6, 9, 8, 7, 4, 5]),
    ),
    "forge_medium_04": (
        HiddenCase(("",), 0),
        HiddenCase(("aaaa",), 1),
        HiddenCase(("abcaef",), 5),
        HiddenCase(("a A",), 3),
        HiddenCase(("dvdf",), 3),
    ),
    "forge_medium_05": (
        HiddenCase(([], []), []),
        HiddenCase((["b", "a", "c"], []), ["a", "b", "c"]),
        HiddenCase((["a", "b", "c"], [["a", "c"], ["b", "c"]]), ["a", "b", "c"]),
        HiddenCase((["a", "b"], [["a", "b"], ["b", "a"]]), []),
        HiddenCase((["a", "b", "c"], [["a", "c"], ["a", "c"]]), ["a", "b", "c"]),
    ),
    "forge_medium_06": (
        HiddenCase(([[5]],), 5),
        HiddenCase(([[1, 2, 3]],), 6),
        HiddenCase(([[1], [4], [2]],), 7),
        HiddenCase(([[1, 3, 1], [1, 5, 1], [4, 2, 1]],), 7),
        HiddenCase(([[0, 9], [0, 0]],), 0),
    ),
    "forge_medium_07": (
        HiddenCase(([],), 0),
        HiddenCase(([[1, 1], [2, 2]],), 0),
        HiddenCase(([[1, 5], [3, 7]],), 6),
        HiddenCase(([[5, 8], [-2, 1], [1, 5]],), 10),
        HiddenCase(([[0, 10], [2, 3], [4, 4]],), 10),
    ),
    "forge_medium_08": (
        HiddenCase(("abc",), "abc"),
        HiddenCase(("3[a]2[bc]",), "aaabcbc"),
        HiddenCase(("2[a2[b]]",), "abbabb"),
        HiddenCase(("10[z]",), "zzzzzzzzzz"),
        HiddenCase(("x2[y]z",), "xyyz"),
    ),
    "forge_medium_09": (
        HiddenCase(([1, 9], 7), [0, 1]),
        HiddenCase(([1, 4, 6, 8], 10), [1, 2]),
        HiddenCase(([5, 5, 5], 10), [0, 1]),
        HiddenCase(([-10, -3, 4, 9], 0), [0, 3]),
        HiddenCase(([0, 8, 2, 6], 8), [0, 1]),
    ),
    "forge_medium_10": (
        HiddenCase(("same", "same", []), 0),
        HiddenCase(("hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]), 4),
        HiddenCase(("hit", "cog", ["hot", "dot", "dog"]), -1),
        HiddenCase(("aaa", "bbb", ["aab", "abb", "bbb", "abb"]), 3),
        HiddenCase(("ab", "cd", ["ad", "cd", "cb"]), 2),
    ),
}


def _freeze(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


HIDDEN_CASES = MappingProxyType(
    {
        task_id: tuple(
            HiddenCase(args=_freeze(case.args), expected=_freeze(case.expected))
            for case in cases
        )
        for task_id, cases in _RAW_CASES.items()
    }
)


def evaluator_sha256() -> str:
    serializable = {
        task_id: [asdict(case) for case in cases]
        for task_id, cases in sorted(HIDDEN_CASES.items())
    }
    payload = json.dumps(serializable, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()
