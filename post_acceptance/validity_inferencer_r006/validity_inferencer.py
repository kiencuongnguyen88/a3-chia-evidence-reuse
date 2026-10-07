from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Mapping, Tuple
import ast, hashlib, json

class InferenceError(RuntimeError):
    pass

def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

class _StripDocstrings(ast.NodeTransformer):
    def visit_Module(self, node):
        node = self.generic_visit(node)
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            node.body = node.body[1:]
        return node
    def visit_FunctionDef(self, node):
        node = self.generic_visit(node)
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            node.body = node.body[1:]
        return node

def _parse(src: str) -> ast.Module:
    try:
        tree = _StripDocstrings().visit(ast.parse(src))
        ast.fix_missing_locations(tree)
        return tree
    except Exception as e:
        raise InferenceError(f"parse_failed:{type(e).__name__}") from e

def _functions_from_tree(tree: ast.Module) -> Dict[str, ast.FunctionDef]:
    return {n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}

def _fn_hash(node: ast.FunctionDef) -> str:
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()

def _module_static_hash(tree: ast.Module) -> str:
    # Imports/module constants are dependency-bearing; top-level function bodies are hashed route-wise.
    static=[n for n in tree.body if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
    return hashlib.sha256(ast.dump(ast.Module(body=static,type_ignores=[]), include_attributes=False).encode()).hexdigest()

def _extract_affine_threshold(operation: ast.FunctionDef) -> int:
    vals=[]
    for n in ast.walk(operation):
        if isinstance(n,ast.Compare) and len(n.ops)==1 and isinstance(n.ops[0],ast.Lt) and len(n.comparators)==1 and isinstance(n.comparators[0],ast.Constant):
            left=n.left
            if isinstance(left,ast.Call) and isinstance(left.func,ast.Attribute) and left.func.attr=='numel':
                vals.append(int(n.comparators[0].value))
    if len(vals)!=1:
        raise InferenceError('affine_dispatch_not_uniquely_resolved')
    return vals[0]

def _extract_reduction_v2_wrapper(setup: ast.FunctionDef) -> ast.FunctionDef:
    candidates=[]
    for n in ast.walk(setup):
        if isinstance(n,ast.FunctionDef) and n.name=='selected':
            calls=[c.func.id for c in ast.walk(n) if isinstance(c,ast.Call) and isinstance(c.func,ast.Name)]
            if calls.count('reduction_fused')>=2:
                candidates.append(n)
    if len(candidates)!=1:
        raise InferenceError('reduction_v2_wrapper_not_uniquely_resolved')
    return candidates[0]

@dataclass(frozen=True)
class GlobalDeps:
    environment: str
    evaluator: str
    oracle: str

@dataclass(frozen=True)
class TypedScope:
    shape: int
    dtype: str='float32'
    layout: str='contiguous'

@dataclass(frozen=True)
class ScopeSnapshot:
    consumer: str
    scope_id: str
    route: str
    local_deps: Mapping[str,str]
    globals: GlobalDeps
    fingerprint: str

@dataclass(frozen=True)
class ValidityDecision:
    consumer: str
    scope_id: str
    reusable: bool
    reason: str
    changed_dependencies: Tuple[str,...]

@dataclass(frozen=True)
class InferenceResult:
    decisions: Tuple[ValidityDecision,...]
    fail_closed: bool
    error: str|None=None

def _coerce_scopes(scopes: Iterable[int|TypedScope]) -> List[TypedScope]:
    out=[]
    for s in scopes:
        out.append(s if isinstance(s,TypedScope) else TypedScope(int(s)))
    return out

def _typed_deps(s: TypedScope) -> Dict[str,str]:
    return {'typed.dtype':_digest(s.dtype),'typed.layout':_digest(s.layout)}

def _snapshot(consumer,scope_id,route,deps,globals_):
    payload={'consumer':consumer,'scope_id':scope_id,'route':route,'deps':dict(sorted(deps.items())),'globals':asdict(globals_)}
    return ScopeSnapshot(consumer,scope_id,route,dict(deps),globals_,_digest(payload))

def affine_snapshots(baseline_src: str, challenger_src: str, scopes: Iterable[int|TypedScope], globals_: GlobalDeps) -> Dict[str,ScopeSnapshot]:
    bt=_parse(baseline_src); ct=_parse(challenger_src)
    base=_functions_from_tree(bt); ch=_functions_from_tree(ct)
    if 'operation' not in base or not {'operation','fused','affine_relu'}.issubset(ch):
        raise InferenceError('affine_required_function_missing')
    threshold=_extract_affine_threshold(ch['operation'])
    common={
      'baseline.module_static':_module_static_hash(bt),
      'baseline.operation':_fn_hash(base['operation']),
      'challenger.module_static':_module_static_hash(ct),
      'challenger.operation':_fn_hash(ch['operation']),
    }
    out={}
    for s in _coerce_scopes(scopes):
        deps=dict(common); deps.update(_typed_deps(s))
        if s.shape < threshold:
            route='small->baseline'
        else:
            route='large->fused'
            deps['challenger.fused']=_fn_hash(ch['fused'])
            deps['challenger.affine_relu']=_fn_hash(ch['affine_relu'])
        out[str(s.shape)]=_snapshot('affine',str(s.shape),route,deps,globals_)
    return out

def reduction_snapshots(operations_src: str, scopes: Iterable[int|TypedScope], implementation: str, globals_: GlobalDeps) -> Dict[str,ScopeSnapshot]:
    tree=_parse(operations_src); f=_functions_from_tree(tree)
    required={'row_sum','reduction_base','reduction_fused','reduction_oracle','setup'}
    if not required.issubset(f): raise InferenceError('reduction_required_function_missing')
    if implementation not in {'v1','v2'}: raise InferenceError('unsupported_reduction_implementation')
    # Deliberately conservative: setup is a dispatch owner. Hashing it prevents reuse if routing changes,
    # even when that causes safe over-invalidation from unrelated bounded setup edits.
    common={
      'operations.module_static':_module_static_hash(tree),
      'operations.setup':_fn_hash(f['setup']),
      'operations.reduction_base':_fn_hash(f['reduction_base']),
      'operations.reduction_oracle':_fn_hash(f['reduction_oracle']),
      'operations.row_sum':_fn_hash(f['row_sum']),
      'operations.reduction_fused':_fn_hash(f['reduction_fused']),
    }
    route='reduction->fused'
    if implementation=='v2':
        common=dict(common)
        common['operations.setup.selected_v2']=_fn_hash(_extract_reduction_v2_wrapper(f['setup']))
        route='reduction->selected_v2->fused_twice'
    out={}
    for s in _coerce_scopes(scopes):
        deps=dict(common); deps.update(_typed_deps(s))
        out[str(s.shape)]=_snapshot('reduction',str(s.shape),route,deps,globals_)
    return out

def compare(old: Mapping[str,ScopeSnapshot], new: Mapping[str,ScopeSnapshot]) -> InferenceResult:
    decisions=[]
    all_ids=sorted(set(old)|set(new), key=lambda x:int(x) if x.isdigit() else x)
    for scope_id in all_ids:
        if scope_id not in old:
            decisions.append(ValidityDecision(new[scope_id].consumer,scope_id,False,'new_scope_no_historical_evidence',('scope',))); continue
        if scope_id not in new:
            decisions.append(ValidityDecision(old[scope_id].consumer,scope_id,False,'scope_removed_or_unresolved',('scope',))); continue
        a,b=old[scope_id],new[scope_id]
        if a.consumer!=b.consumer:
            decisions.append(ValidityDecision(a.consumer,scope_id,False,'consumer_changed',('consumer',))); continue
        changed=[]
        if a.route!=b.route: changed.append('route')
        for k in sorted(set(a.local_deps)|set(b.local_deps)):
            if a.local_deps.get(k)!=b.local_deps.get(k): changed.append('local:'+k)
        for k in ('environment','evaluator','oracle'):
            if getattr(a.globals,k)!=getattr(b.globals,k): changed.append('global:'+k)
        decisions.append(ValidityDecision(a.consumer,scope_id,len(changed)==0,'unchanged_dependency_signature' if not changed else 'dependency_changed',tuple(changed)))
    return InferenceResult(tuple(decisions),False)

def infer_or_fail_closed(builder,*args,**kwargs)->InferenceResult:
    try: return builder(*args,**kwargs)
    except Exception as e: return InferenceResult(tuple(),True,str(e))

def reusable_ids(result:InferenceResult)->List[str]: return [d.scope_id for d in result.decisions if d.reusable]
def invalid_ids(result:InferenceResult)->List[str]: return [d.scope_id for d in result.decisions if not d.reusable]
