"""Shared development planner. No GPU imports; evidence is explicit, never implicit."""
from dataclasses import dataclass, asdict
import hashlib, json, math

def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

@dataclass(frozen=True)
class Scope:
    path: str
    shape: int
    dtype: str
    layout: str
    code: str
    environment: str
    evaluator: str
    oracle: str

@dataclass
class Evidence:
    scope: Scope
    candidate_bundle: str
    objective: dict
    raw_artifact: str
    raw_sha256: str
    conclusion_scope: str
    provenance: dict
    live_vs_replay: str
    speedup: float
    sampled_gpu_seconds: float

    def to_dict(self): return asdict(self)


def evaluate(values, weights, complete=True):
    active = [n for n,w in weights.items() if w > 0]
    known = [n for n in active if n in values]
    if any(values[n] < .95 for n in known): return 'REJECT'
    if len(known) != len(active): return 'UNRESOLVED'
    score = math.exp(sum(weights[n]*math.log(values[n]) for n in active)/sum(weights[n] for n in active))
    return 'PROMOTE' if score >= 1.15 else 'REJECT'


def cache_key(method, scope, bundle, protocol):
    if method == 'B1':
        # The Epoch001 user-defined tag policy: resolved implementation + entire protocol.
        return digest({'n':scope.shape,'path':scope.path,'implementation':scope.code,'protocol':protocol})
    if method in ('B2','B3','NO_SCOPE'):
        return digest({'scope':asdict(scope), 'bundle':bundle})
    return digest(asdict(scope))


def choose(method, pending, weights, prior):
    if method in ('B3','NO_SCOPE'):
        # Ordinary largest weighted problem first, then safe early rejection.
        return max(pending, key=lambda n: (weights[n]*n,n))
    if method == 'FULL_A':
        # Decision impact per estimated measured cost; old evidence only ranks, never certifies a changed scope.
        def priority(n):
            p=prior.get(n, {})
            risk=1/max(abs(p.get('speedup',1)-.95),.01)
            return (weights[n]*risk/max(p.get('cost',.01),.00001),n)
        return max(pending,key=priority)
    return min(pending)


def can_stop(method, values, weights):
    return method in ('B3','FULL_A','NO_SCOPE') and evaluate(values,weights) == 'REJECT'
