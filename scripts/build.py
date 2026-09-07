#!/usr/bin/env python3
import pathlib, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]

def build():
    (ROOT/'build').mkdir(exist_ok=True)
    for name,flags in [('gemm',[]),('gemm-mutant',['-DTAIL_MUTATION=1'])]:
        subprocess.run(['g++','-std=c++17','-O3','-Wall','-Wextra','-Werror',*flags,
                        str(ROOT/'src/gemm.cpp'),'-o',str(ROOT/'build'/name)],check=True)
    return ROOT/'build/gemm'

if __name__=='__main__': print(build())
