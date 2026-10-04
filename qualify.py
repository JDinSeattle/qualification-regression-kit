"""Independent exact oracle, complete result accounting, paired uncertainty gate."""
import json
import math
import os
import random
import signal
import statistics
import subprocess
import time


def oracle(m, n, k, seed):
    # Integer dot products divided once; SUT accumulates floating point row updates.
    a=[(i*17+seed*13)%19-9 for i in range(m*k)]
    b=[(i*11+seed*7)%23-11 for i in range(k*n)]
    columns=[b[j::n] for j in range(n)]
    return [sum(x*y for x,y in zip(a[i*k:(i+1)*k],col))/64
            for i in range(m) for col in columns]


def check(payload, expected, repeats):
    try:
        values=payload['values']; times=payload['kernel_us']
        if type(payload['protocol']) is not int or payload['protocol']!=1:
            return 'malformed'
        if not isinstance(values,list) or not isinstance(times,list): return 'malformed'
        if len(values)!=len(expected) or len(times)!=repeats:
            return 'missing_data'
        if any(type(x) not in (int,float) or not math.isfinite(x) for x in values+times):
            return 'nonfinite'
        if any(t<=0 for t in times): return 'invalid_timing'
        if any(x!=y for x,y in zip(values,expected)): return 'wrong_answer'
        return 'pass'
    except (KeyError,TypeError,ValueError,OverflowError): return 'malformed'


def execute(argv, expected, repeats=1, timeout=5,input_data=None):
    start=time.monotonic_ns()
    record={'argv':list(map(str,argv)),'status':'not_run'}
    try:
        p=subprocess.Popen(argv,stdin=subprocess.PIPE if input_data is not None else None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
        try:
            stdout,stderr=p.communicate(input=input_data,timeout=timeout)
        except subprocess.TimeoutExpired:
            # Kill the process group, including descendants retaining our output pipes.
            try: os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            stdout,stderr=p.communicate(timeout=2)
            record.update(status='timeout',returncode=p.returncode,stdout=stdout,stderr=stderr,
                          child_reaped=True,process_group_signalled=True)
            return record
        record.update(returncode=p.returncode,stderr=stderr,stdout=stdout,child_reaped=True)
        if p.returncode: record['status']='process_failure'
        else:
            try:
                payload=json.loads(stdout)
                record['status']=check(payload,expected,repeats)
                record['kernel_us']=payload.get('kernel_us',[])
            except (ValueError,TypeError,AttributeError): record['status']='malformed'
    except OSError as e: record.update(status='spawn_failure',error=str(e))
    finally: record['end_to_end_us']=(time.monotonic_ns()-start)/1000
    return record


def compare(pairs, min_pairs=10, practical=0.05):
    if len(pairs)<min_pairs: return {'decision':'uncertain','reason':'insufficient_pairs'}
    if any(len(p)!=2 or any(not math.isfinite(v) or v<=0 for v in p) for p in pairs):
        return {'decision':'invalid','reason':'invalid_sample'}
    ratios=[c/b for b,c in pairs]; rng=random.Random(418)
    boot=sorted(statistics.median(rng.choices(ratios,k=len(ratios))) for _ in range(2000))
    lo,hi=boot[49],boot[1949]
    decision='regression' if lo>1+practical else 'improvement' if hi<1-practical else 'uncertain'
    return {'decision':decision,'candidate_over_control_median':statistics.median(ratios),
            'bootstrap_95pct':[lo,hi],'valid_pairs':len(pairs),'practical_threshold':practical}


def require_complete(records, expected_ids):
    ids=[r['id'] for r in records]
    return len(ids)==len(set(ids)) and set(ids)==set(expected_ids) and all(r['status']=='pass' for r in records)

def minimize(binary,shape,seed):
    """Delete actual matrix rows/columns/K ranges; independently reconfirm both workers.

    Fixed nonzero input keeps the known injected tail observable. A process or
    parse failure cannot be accepted as a smaller wrong-answer counterexample.
    """
    m,n,k=shape
    a=[[2]*k for _ in range(m)]; b=[[3]*n for _ in range(k)]
    steps=[]
    def evaluate(left,right):
        dims=[len(left),len(right[0]),len(right)]
        expected=[sum(left[i][q]*right[q][j] for q in range(dims[2]))
                  for i in range(dims[0]) for j in range(dims[1])]
        data=' '.join(str(x) for row in left+right for x in row)
        common=[*map(str,dims),'1',str(seed),'stdin']
        reference=execute([str(binary),'reference',*common],expected,input_data=data)
        candidate=execute([str(binary),'optimized',*common],expected,input_data=data)
        steps.append({'trial':dims,'reference_status':reference['status'],
                      'candidate_status':candidate['status']})
        return reference['status']=='pass' and candidate['status']=='wrong_answer'
    if not evaluate(a,b):
        raise ValueError('initial input is not a confirmed wrong-answer counterexample')
    for axis in range(3):
        while True:
            length=[len(a),len(b[0]),len(b)][axis]
            changed=False
            for removed in range(max(1,length//2),0,-1):
                for start in range(length-removed+1):
                    keep=[i for i in range(length) if not start<=i<start+removed]
                    if not keep: continue
                    if axis==0: left=[a[i] for i in keep]; right=b
                    elif axis==1: left=a; right=[[row[i] for i in keep] for row in b]
                    else: left=[[row[i] for i in keep] for row in a]; right=[b[i] for i in keep]
                    if evaluate(left,right): a,b=left,right;changed=True;break
                if changed: break
            if not changed: break
    return {'initial_shape':list(shape),'minimal_shape':[len(a),len(b[0]),len(b)],
            'a':a,'b':b,'expected':[sum(a[0][q]*b[q][0] for q in range(len(b)))],
            'steps':steps,'seed':seed}


def compare_speedup(pairs,seed=418):
    """Paired geometric speedup with resampling of whole matched pairs."""
    if not pairs or any(len(p)!=2 or any(not math.isfinite(x) or x<=0 for x in p) for p in pairs):
        return {'decision':'invalid'}
    logs=[math.log(control/repaired) for control,repaired in pairs]
    rng=random.Random(seed)
    draws=sorted(math.exp(statistics.mean(rng.choices(logs,k=len(logs)))) for _ in range(2000))
    lo,hi=draws[49],draws[1949]
    return {'geomean_speedup':math.exp(statistics.mean(logs)), 'bootstrap_95pct':[lo,hi],
            'decision':'improvement' if lo>1.05 else 'regression' if hi<1/1.05 else 'uncertain',
            'valid_pairs':len(pairs),'seed':seed}
