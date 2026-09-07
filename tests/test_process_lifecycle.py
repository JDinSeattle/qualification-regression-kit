import json, os, pathlib, subprocess, sys, tempfile, time, unittest
from qualify import check, execute

class ProcessLifecycleTests(unittest.TestCase):
    def test_protocol_and_numeric_types_fail_closed(self):
        for protocol in [True,1.0,'1',None]:
            self.assertNotEqual(check({'protocol':protocol,'values':[1],'kernel_us':[1]},[1],1),'pass')
        self.assertNotEqual(check({'protocol':1,'values':[10**1000],'kernel_us':[1]},[1],1),'pass')
    def test_timeout_terminates_descendant_and_keeps_diagnostic(self):
        with tempfile.TemporaryDirectory() as d:
            marker=pathlib.Path(d)/'descendant-completed'
            child=f'import time,pathlib;time.sleep(.7);pathlib.Path({str(marker)!r}).write_text("escaped")'
            parent=f'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",{child!r}]);print("before timeout",flush=True);time.sleep(30)'
            started=time.monotonic();r=execute([sys.executable,'-c',parent],[],timeout=.15)
            self.assertEqual(r['status'],'timeout'); self.assertIn('before timeout',r['stdout'])
            self.assertTrue(r['child_reaped']);self.assertTrue(r['process_group_signalled'])
            self.assertLess(time.monotonic()-started,2);self.assertGreater(r['end_to_end_us'],0)
            time.sleep(.8);self.assertFalse(marker.exists())
    def test_malformed_scalar_output(self):
        self.assertEqual(execute([sys.executable,'-c','print("null")'],[])['status'],'malformed')
