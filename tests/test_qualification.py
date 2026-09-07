import math, pathlib, subprocess, sys, unittest
from qualify import check, compare, execute, oracle, require_complete
from scripts.build import build

class QualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.binary=build()
    def test_hand_calculated_oracle(self):
        self.assertEqual(oracle(1,1,1,0),[99/64])
    def test_bad_measurements_never_pass(self):
        for p in [{},{'protocol':1,'values':[float('nan')],'kernel_us':[1]},
                  {'protocol':1,'values':[],'kernel_us':[1]},
                  {'protocol':1,'values':[1],'kernel_us':[0]}]:
            self.assertNotEqual(check(p,[1],1),'pass')
    def test_duplicate_and_missing_records_reject(self):
        self.assertFalse(require_complete([{'id':'a','status':'pass'}],['a','b']))
        self.assertFalse(require_complete([{'id':'a','status':'pass'}]*2,['a']))
    def test_timeout_exit_and_missing_binary(self):
        self.assertEqual(execute([sys.executable,'-c','import time;time.sleep(2)'],[],timeout=.05)['status'],'timeout')
        self.assertEqual(execute([sys.executable,'-c','raise SystemExit(7)'],[])['status'],'process_failure')
        self.assertEqual(execute(['/nonexistent/qualification-worker'],[])['status'],'spawn_failure')
    def test_uncertainty_and_regression(self):
        self.assertEqual(compare([(1,1)]*20)['decision'],'uncertain')
        self.assertEqual(compare([(1,1.3)]*20)['decision'],'regression')
        self.assertEqual(compare([(1,.5)]*20)['decision'],'improvement')
        self.assertEqual(compare([(1,.5)])['decision'],'uncertain')
        self.assertEqual(compare([(1,float('nan'))]*20)['decision'],'invalid')
    def test_mutant_and_repair(self):
        for k in [1,7,8,9,16,17]:
            args=['optimized','3','5',str(k),'1','7','generated']
            self.assertEqual(execute([str(self.binary),*args],oracle(3,5,k,7))['status'],'pass')
            status=execute([str(self.binary)+'-mutant',*args],oracle(3,5,k,7))['status']
            self.assertEqual(status,'pass' if k%8==0 else 'wrong_answer')
    def test_input_bounds(self):
        for dims in [('0','2','3'),('513','2','3'),('2x','2','3')]:
            p=subprocess.run([self.binary,'optimized',*dims,'1','0','generated'],capture_output=True)
            self.assertEqual(p.returncode,2)
    def test_supplied_matrix(self):
        p=subprocess.run([self.binary,'optimized','1','1','2','1','0','stdin'],input='2 3 4 5',capture_output=True,text=True)
        self.assertEqual(check(__import__('json').loads(p.stdout),[23],1),'pass')
    def test_undefined_behavior_sanitizer_boundaries(self):
        root=self.binary.parent.parent; sanitized=root/'build/gemm-ubsan'
        subprocess.run(['g++','-std=c++17','-O1','-fsanitize=undefined','-fno-sanitize-recover=all',str(root/'src/gemm.cpp'),'-o',str(sanitized)],check=True)
        for m,n,k in [(1,1,1),(1,512,1),(512,1,1),(17,31,13),(8,8,9)]:
            self.assertEqual(execute([str(sanitized),'optimized',str(m),str(n),str(k),'1','7','generated'],oracle(m,n,k,7))['status'],'pass')

if __name__=='__main__': unittest.main()
