from __future__ import annotations

import json
from typing import Any


def dumps_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=True, sort_keys=True, indent=2)
