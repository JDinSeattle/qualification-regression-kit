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


def execute(argv, expected, repeats=1, timeout=5):
    start=time.monotonic_ns()
    record={'argv':list(map(str,argv)),'status':'not_run'}
    try:
        p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
        try:
            stdout,stderr=p.communicate(timeout=timeout)
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
    initial=list(shape); shape=list(shape); steps=[]
    for axis in range(3):
        trial=list(shape); trial[axis]=1
        result=execute([str(binary),'optimized',*map(str,trial),'1',str(seed),'generated'],oracle(*trial,seed))
        steps.append({'trial':trial,'status':result['status']})
        if result['status']=='wrong_answer': shape=trial
    return {'initial_shape':initial,'minimal_shape':shape,'steps':steps,'seed':seed}
