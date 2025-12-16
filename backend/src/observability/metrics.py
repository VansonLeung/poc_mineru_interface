from __future__ import annotations

import statistics
from collections import Counter, deque
from typing import Deque, Dict


class MetricsRecorder:
    def __init__(self, window: int = 200) -> None:
        self.window = window
        self.requests: Deque[float] = deque(maxlen=window)
        self.status_codes: Counter[int] = Counter()

    def record(self, status_code: int, duration_ms: float) -> None:
        self.requests.append(duration_ms)
        self.status_codes[status_code] += 1

    def snapshot(self) -> Dict[str, float]:
        if self.requests:
            p95 = statistics.quantiles(self.requests, n=20)[-1]
            avg = statistics.fmean(self.requests)
        else:
            p95 = 0.0
            avg = 0.0
        total = sum(self.status_codes.values())
        failures = sum(count for code, count in self.status_codes.items() if code >= 500)
        return {
            "requests_total": total,
            "failures_total": failures,
            "latency_avg_ms": round(avg, 2),
            "latency_p95_ms": round(p95, 2),
        }


metrics = MetricsRecorder()
