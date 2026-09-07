#!/usr/bin/env python3
import argparse, json, os, pathlib, random, signal, statistics, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from evidence import command, digest, fresh, seal, write
from qualify import compare, execute, minimize, oracle
from scripts.build import build

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='.runs/latest'); args=ap.parse_args()
    out=fresh(ROOT,args.out)
    binary=build(); rng=random.Random(20260907)
    workloads=[(1,1,1),(17,31,13),(129,257,65),(1,256,256),(32,64,32),(128,128,128)]
    records=[]
    for shape in workloads:
      for seed in [7,11,19]:
        expected=oracle(*shape,seed)
        order=['control','candidate','fixed']; rng.shuffle(order)
        for variant in order:
            exe=str(binary)+('-mutant' if variant=='candidate' else '')
            argv=[exe,'reference' if variant=='control' else 'optimized',*map(str,shape),'3',str(seed),'generated']
            r=execute(argv,expected,3)
            r.update(id=f'{shape}-{seed}-{variant}',shape=shape,seed=seed,variant=variant)
            records.append(r)
    expected_failures=sum(r['variant']=='candidate' and r['shape'][2]%8!=0 for r in records)
    assert all(r['status']==('wrong_answer' if r['variant']=='candidate' and r['shape'][2]%8 else 'pass') for r in records)
    minimal=execute([str(binary)+'-mutant','optimized','1','1','1','1','0','generated'],oracle(1,1,1,0))
    write(out/'minimal_failure.json',minimal)
    assert minimal['status']=='wrong_answer'
    reduction=minimize(str(binary)+'-mutant',[17,31,13],7)
    assert reduction['minimal_shape']==[1,1,1]
    write(out/'reduction.json',reduction)
    # Independent, bounded process faults. These are executor tests, not GEMM defects.
    faults={
        'timeout':execute([sys.executable,'-c','import time;time.sleep(3)'],[],timeout=.1),
        'abnormal_exit':execute([sys.executable,'-c','raise SystemExit(9)'],[]),
        'missing_result':execute([sys.executable,'-c','print("{}")'],[]),
        'memory_limit':execute([sys.executable,'-c','import resource;resource.setrlimit(resource.RLIMIT_AS,(64*1024**2,64*1024**2));bytearray(128*1024**2)'],[]),
    }
    p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']); p.send_signal(signal.SIGTERM); p.wait(timeout=2)
    faults['cancel']={'returncode':p.returncode,'status':'cancelled','child_reaped':p.poll() is not None}
    assert all(r['status']!='pass' for r in faults.values()) and p.returncode<0
    paired=[]; performance=[]
    for rep in range(20):
        order=['reference','optimized']; rng.shuffle(order); pair={}
        for mode in order:
            r=execute([str(binary),mode,'128','128','128','8','7','generated'],oracle(128,128,128,7),8)
            assert r['status']=='pass'; pair[mode]=statistics.median(r['kernel_us'])
            r.update(pair=rep,mode=mode); performance.append(r)
        paired.append((pair['reference'],pair['optimized']))
    (out/'correctness.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    (out/'performance.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in performance))
    write(out/'faults.json',faults)
    result={'correctness_records':len(records),'expected_mutant_failures':expected_failures,
            'control_and_fixed_pass':sum(r['status']=='pass' for r in records if r['variant']!='candidate'),
            'performance':compare(paired),'matrix':workloads,'seed':20260907}
    write(out/'summary.json',result)
    (out/'disassembly.txt').write_text(command(['objdump','-d','-C',str(binary)]))
    seal(ROOT,out,{'compiler':command(['g++','--version']).splitlines()[0],
         'flags':'-std=c++17 -O3 -Wall -Wextra -Werror; no fast-math',
         'binary_sha256':digest(binary),'mutant_sha256':digest(str(binary)+'-mutant'),
         'timing':'steady_clock microseconds; one warmup; allocations/output excluded; process e2e separately retained',
         'clock_control':'none; shared host; no GPU execution'})
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
