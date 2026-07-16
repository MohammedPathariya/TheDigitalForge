"""Evaluator-only cases.

This module must never be imported by a model-facing prompt builder. Cases are tuples of
frozen records so an in-process caller cannot mutate the canonical evaluator data.
"""

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class HiddenCase:
    args: tuple[Any, ...]
    expected: Any


_RAW_CASES = {
    "forge_easy_01": (
        HiddenCase(
            ([" sku-1, 2 ", "#skip", "", "sku-1,-1", "bad", "sku-2, x"],), {"sku-1": 1}
        ),
        HiddenCase((["A,1", "B,2", "A,3"],), {"A": 4, "B": 2}),
        HiddenCase(([" ,5", "C, 0", "C, -2"],), {"C": -2}),
        HiddenCase(([" # comment", "D,004", "D,+1"],), {"D": 5}),
    ),
    "forge_easy_02": (
        HiddenCase(
            ({"email": " USER@Example.COM ", "display_name": " Ada ", "active": "no"},),
            {"email": "user@example.com", "display_name": "Ada", "active": False},
        ),
        HiddenCase(
            ({"email": "sam@example.com", "display_name": "   "},),
            {"email": "sam@example.com", "display_name": "sam", "active": True},
        ),
        HiddenCase(
            ({"active": 0},), {"email": "", "display_name": "unknown", "active": False}
        ),
        HiddenCase(
            ({"email": "  @example.com ", "active": " FALSE "},),
            {"email": "@example.com", "display_name": "unknown", "active": False},
        ),
    ),
    "forge_easy_03": (
        HiddenCase(
            (
                {
                    "title": "token leaked",
                    "labels": [],
                    "component": "billing",
                    "priority": "p0",
                },
            ),
            "security",
        ),
        HiddenCase(
            ({"title": "refund failed", "labels": ["bug"], "component": "Checkout"},),
            "payments",
        ),
        HiddenCase(
            (
                {
                    "title": "site down",
                    "labels": [],
                    "component": "web",
                    "priority": "P1",
                },
            ),
            "urgent-support",
        ),
        HiddenCase(({"title": "how do I export?", "labels": ["question"]},), "support"),
    ),
    "forge_easy_04": (
        HiddenCase(
            ({"FEATURE_SEARCH": "true", "FEATURE_BETA__UI": " off ", "OTHER": "1"},),
            {"search": True, "beta.ui": False},
        ),
        HiddenCase(
            ({"FEATURE_A": "yes", "FEATURE_B": "maybe", "FEATURE_C": "0"},),
            {"a": True, "c": False},
        ),
        HiddenCase(({"FF_X": "on", "FF_Y": "no"}, "FF_"), {"x": True, "y": False}),
        HiddenCase(({},), {}),
    ),
    "forge_easy_05": (
        HiddenCase(
            (
                [
                    {"type": "feat", "scope": "api", "summary": "add tokens"},
                    {"type": "fix", "summary": " trim input "},
                ],
            ),
            {
                "feature": ["api: add tokens"],
                "fix": ["trim input"],
                "docs": [],
                "other": [],
            },
        ),
        HiddenCase(
            (
                [
                    {"type": "docs", "scope": "", "summary": "Readme"},
                    {"type": "chore", "scope": "ci", "summary": "cache"},
                ],
            ),
            {"feature": [], "fix": [], "docs": ["Readme"], "other": ["ci: cache"]},
        ),
        HiddenCase(
            ([{"type": "feat", "summary": "   "}, {"summary": "ship"}],),
            {"feature": [], "fix": [], "docs": [], "other": ["ship"]},
        ),
        HiddenCase(([],), {"feature": [], "fix": [], "docs": [], "other": []}),
    ),
    "forge_easy_06": (
        HiddenCase(
            ({"db_password": "p", "nested": {"api_key": "k", "name": "svc"}},),
            {"db_password": "***", "nested": {"api_key": "***", "name": "svc"}},
        ),
        HiddenCase(
            ({"items": [{"token": "abc"}, {"value": 3}]},),
            {"items": [{"token": "***"}, {"value": 3}]},
        ),
        HiddenCase(
            ({"SecretValue": "x", "safe": True},), {"SecretValue": "***", "safe": True}
        ),
        HiddenCase(({},), {}),
    ),
    "forge_easy_07": (
        HiddenCase(
            (
                [
                    {"team": "api", "age_hours": 25, "status": "open"},
                    {"team": "api", "age_hours": 10, "status": "open"},
                ],
                24,
            ),
            {"api": 1},
        ),
        HiddenCase(
            (
                [
                    {"team": " ", "age_hours": 5, "status": "new"},
                    {"age_hours": 7, "status": "closed"},
                ],
                4,
            ),
            {"unassigned": 1},
        ),
        HiddenCase(
            (
                [
                    {"team": "web", "age_hours": "9", "status": "OPEN"},
                    {"team": "web", "age_hours": "x"},
                ],
                8,
            ),
            {"web": 1},
        ),
        HiddenCase(([], 1), {}),
    ),
    "forge_easy_08": (
        HiddenCase(("Hello, Forge!", []), "hello-forge"),
        HiddenCase(("Hello Forge", ["hello-forge", "hello-forge-2"]), "hello-forge-3"),
        HiddenCase((" !!! ", []), "item"),
        HiddenCase(("A__B  C", ["a-b-c"]), "a-b-c-2"),
    ),
    "forge_easy_09": (
        HiddenCase(
            ("attempts=3; backoff=10; jitter=2",),
            {"attempts": 3, "backoff": 10, "jitter": 2},
        ),
        HiddenCase(
            ("attempts=x; attempts=4; other=9",),
            {"attempts": 4, "backoff": 0, "jitter": 0},
        ),
        HiddenCase(
            ("backoff=-1; jitter=0005; =3",), {"attempts": 1, "backoff": 0, "jitter": 5}
        ),
        HiddenCase(("",), {"attempts": 1, "backoff": 0, "jitter": 0}),
    ),
    "forge_easy_10": (
        HiddenCase(
            (
                [{"quantity": 2, "unit_cents": 150}, {"quantity": 1, "unit_cents": 99}],
                0.07,
            ),
            {"subtotal_cents": 399, "tax_cents": 28, "total_cents": 427},
        ),
        HiddenCase(
            (
                [{"quantity": 0, "unit_cents": 999}, {"quantity": 3, "unit_cents": -1}],
                0.2,
            ),
            {"subtotal_cents": 0, "tax_cents": 0, "total_cents": 0},
        ),
        HiddenCase(
            ([{"quantity": 1}], 0.5),
            {"subtotal_cents": 0, "tax_cents": 0, "total_cents": 0},
        ),
        HiddenCase(([], 0.1), {"subtotal_cents": 0, "tax_cents": 0, "total_cents": 0}),
    ),
    "forge_medium_01": (
        HiddenCase(
            (
                [{"id": "o1", "total_cents": 500}, {"id": "o2", "total_cents": 300}],
                [
                    {"order_id": "o1", "amount_cents": 200},
                    {"order_id": "o1", "amount_cents": 300},
                    {"order_id": "o2", "amount_cents": 500},
                ],
            ),
            [
                {"id": "o1", "paid_cents": 500, "balance_cents": 0, "status": "paid"},
                {
                    "id": "o2",
                    "paid_cents": 500,
                    "balance_cents": -200,
                    "status": "overpaid",
                },
            ],
        ),
        HiddenCase(
            (
                [{"id": "a", "total_cents": 100}],
                [{"order_id": "a", "amount_cents": 40, "status": "failed"}],
            ),
            [{"id": "a", "paid_cents": 0, "balance_cents": 100, "status": "unpaid"}],
        ),
        HiddenCase(
            (
                [{"id": "b", "total_cents": 100}],
                [{"order_id": "b", "amount_cents": 40, "status": "CAPTURED"}],
            ),
            [{"id": "b", "paid_cents": 40, "balance_cents": 60, "status": "partial"}],
        ),
        HiddenCase(([], []), []),
    ),
    "forge_medium_02": (
        HiddenCase(
            ({"steps": [{"id": "build"}, {"id": "test", "needs": ["build"]}]},), []
        ),
        HiddenCase(
            ({"steps": [{"id": "a"}, {"id": "a"}, {"id": "b", "needs": ["c", "b"]}]},),
            ["duplicate step: a", "missing dependency: b -> c", "self dependency: b"],
        ),
        HiddenCase(
            ({"steps": [{"id": "a", "needs": ["b"]}, {"id": "b", "needs": ["a"]}]},),
            ["cycle detected"],
        ),
        HiddenCase(
            ({"steps": [{"id": " "}, {"id": "x", "needs": [" "]}]},),
            ["missing dependency: x ->  "],
        ),
    ),
    "forge_medium_03": (
        HiddenCase(
            (
                {"profile": {"name": "Ada"}},
                [{"op": "set", "path": "/profile/email", "value": "a@example.com"}],
            ),
            {"profile": {"name": "Ada", "email": "a@example.com"}},
        ),
        HiddenCase(
            (
                {"a": {"b": 1}, "x": 2},
                [
                    {"op": "remove", "path": "/a/b"},
                    {"op": "remove", "path": "/missing"},
                ],
            ),
            {"a": {}, "x": 2},
        ),
        HiddenCase(
            ({}, [{"op": "set", "path": "/a/b/c", "value": 3}]), {"a": {"b": {"c": 3}}}
        ),
        HiddenCase(
            (
                {"a": 1},
                [
                    {"op": "copy", "path": "/b", "value": 2},
                    {"op": "set", "path": "bad", "value": 9},
                ],
            ),
            {"a": 1},
        ),
    ),
    "forge_medium_04": (
        HiddenCase(
            (
                {"sku1": 5},
                [
                    {"id": "r1", "sku": "sku1", "quantity": 3},
                    {"id": "r2", "sku": "sku1", "quantity": 4},
                ],
            ),
            [
                {
                    "id": "r1",
                    "sku": "sku1",
                    "requested": 3,
                    "allocated": 3,
                    "status": "filled",
                },
                {
                    "id": "r2",
                    "sku": "sku1",
                    "requested": 4,
                    "allocated": 2,
                    "status": "partial",
                },
            ],
        ),
        HiddenCase(
            ({"a": 0}, [{"id": "x", "sku": "a", "quantity": 1}]),
            [
                {
                    "id": "x",
                    "sku": "a",
                    "requested": 1,
                    "allocated": 0,
                    "status": "backordered",
                }
            ],
        ),
        HiddenCase(
            ({"a": 2}, [{"id": "bad", "sku": "a", "quantity": 0}]),
            [
                {
                    "id": "bad",
                    "sku": "a",
                    "requested": 0,
                    "allocated": 0,
                    "status": "rejected",
                }
            ],
        ),
        HiddenCase(({}, []), []),
    ),
    "forge_medium_05": (
        HiddenCase(
            (["api", "web", "db"], [["db", "api"], ["api", "web"]]),
            ["db", "api", "web"],
        ),
        HiddenCase((["b", "a", "c"], []), ["a", "b", "c"]),
        HiddenCase((["a", "b"], [["a", "b"], ["b", "a"]]), []),
        HiddenCase(
            (["a", "b", "c"], [["x", "a"], ["a", "c"], ["a", "c"]]), ["a", "b", "c"]
        ),
    ),
    "forge_medium_06": (
        HiddenCase(
            (
                {"name": "", "emails": ["A@EXAMPLE.COM"], "metadata": {"tier": "pro"}},
                {
                    "name": "Ada",
                    "emails": ["a@example.com", "b@example.com"],
                    "metadata": {"region": "us", "tier": "free"},
                },
            ),
            {
                "name": "Ada",
                "emails": ["a@example.com", "b@example.com"],
                "metadata": {"region": "us", "tier": "pro"},
            },
        ),
        HiddenCase(
            ({"name": "Primary", "age": None}, {"name": "Secondary", "age": 30}),
            {"name": "Primary", "age": 30, "emails": [], "metadata": {}},
        ),
        HiddenCase(
            ({}, {"emails": [" ", "X@Y.COM"]}), {"emails": ["x@y.com"], "metadata": {}}
        ),
        HiddenCase(
            ({"metadata": "bad"}, {"metadata": {"a": 1}}),
            {"metadata": {"a": 1}, "emails": []},
        ),
    ),
    "forge_medium_07": (
        HiddenCase(
            (
                [
                    {
                        "time": "2026-01-01T00:00",
                        "service": "api",
                        "status": "down",
                        "message": "start",
                    },
                    {
                        "time": "2026-01-01T00:01",
                        "service": "api",
                        "status": "down",
                        "message": " still ",
                    },
                    {"time": "2026-01-01T00:02", "service": "api", "status": "up"},
                ],
            ),
            [
                {
                    "service": "api",
                    "status": "down",
                    "time": "2026-01-01T00:00",
                    "count": 2,
                    "messages": ["start", "still"],
                },
                {
                    "service": "api",
                    "status": "up",
                    "time": "2026-01-01T00:02",
                    "count": 1,
                    "messages": [],
                },
            ],
        ),
        HiddenCase(
            (
                [
                    {"time": "2", "service": "b", "status": "x"},
                    {"time": "1", "service": "b", "status": "x"},
                ],
            ),
            [{"service": "b", "status": "x", "time": "1", "count": 2, "messages": []}],
        ),
        HiddenCase(
            (
                [
                    {"time": "1", "service": "a", "status": "x"},
                    {"time": "1", "service": "b", "status": "x"},
                ],
            ),
            [
                {
                    "service": "a",
                    "status": "x",
                    "time": "1",
                    "count": 1,
                    "messages": [],
                },
                {
                    "service": "b",
                    "status": "x",
                    "time": "1",
                    "count": 1,
                    "messages": [],
                },
            ],
        ),
        HiddenCase(([],), []),
    ),
    "forge_medium_08": (
        HiddenCase(
            (
                [
                    {"op": "put", "key": "a"},
                    {"op": "put", "key": "b"},
                    {"op": "get", "key": "a"},
                    {"op": "put", "key": "c"},
                ],
                2,
            ),
            ["a", "c"],
        ),
        HiddenCase(
            (
                [
                    {"op": "put", "key": "a"},
                    {"op": "put", "key": "a"},
                    {"op": "put", "key": "b"},
                ],
                2,
            ),
            ["a", "b"],
        ),
        HiddenCase(([{"op": "put", "key": "a"}], 0), []),
        HiddenCase(
            ([{"op": "get", "key": "missing"}, {"op": "bad", "key": "x"}], 3), []
        ),
    ),
    "forge_medium_09": (
        HiddenCase(
            (
                [
                    {"endpoint": "/a", "status": 500, "time": "t1"},
                    {"endpoint": "/a", "status": 500, "time": "t2"},
                    {"endpoint": "/b", "status": 404, "time": "t3"},
                ],
            ),
            [
                {
                    "endpoint": "/a",
                    "status": 500,
                    "count": 2,
                    "first_time": "t1",
                    "last_time": "t2",
                },
                {
                    "endpoint": "/b",
                    "status": 404,
                    "count": 1,
                    "first_time": "t3",
                    "last_time": "t3",
                },
            ],
        ),
        HiddenCase(
            (
                [
                    {"endpoint": "/a", "status": 200},
                    {"endpoint": "/a", "status": 500, "time": "x"},
                ],
            ),
            [
                {
                    "endpoint": "/a",
                    "status": 500,
                    "count": 1,
                    "first_time": "x",
                    "last_time": "x",
                }
            ],
        ),
        HiddenCase(
            ([{"status": 503}, {"status": "500"}],),
            [
                {
                    "endpoint": "unknown",
                    "status": 503,
                    "count": 1,
                    "first_time": "",
                    "last_time": "",
                }
            ],
        ),
        HiddenCase(([],), []),
    ),
    "forge_medium_10": (
        HiddenCase(
            (
                {
                    "id": 123,
                    "type": "User Created",
                    "actor": {"email": " A@EXAMPLE.COM "},
                    "resources": [{"kind": " user ", "id": " 42 "}],
                },
            ),
            {
                "event_id": "123",
                "event_type": "user_created",
                "actor_email": "a@example.com",
                "resources": [{"kind": "user", "id": "42"}],
            },
        ),
        HiddenCase(
            (
                {
                    "type": "PING",
                    "resources": [{"kind": "", "id": "1"}, {"kind": "org", "id": None}],
                },
            ),
            {
                "event_id": "",
                "event_type": "ping",
                "actor_email": "",
                "resources": [{"kind": "org", "id": "None"}],
            },
        ),
        HiddenCase(
            ({},),
            {"event_id": "", "event_type": "", "actor_email": "", "resources": []},
        ),
        HiddenCase(
            ({"id": "e", "type": "A B C", "actor": {}},),
            {
                "event_id": "e",
                "event_type": "a_b_c",
                "actor_email": "",
                "resources": [],
            },
        ),
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


def to_jsonable(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
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
        task_id: [
            {
                "args": to_jsonable(case.args),
                "expected": to_jsonable(case.expected),
            }
            for case in cases
        ]
        for task_id, cases in sorted(HIDDEN_CASES.items())
    }
    payload = json.dumps(serializable, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()
