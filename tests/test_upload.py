import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_upload import verify,payload

class UploadTests(unittest.TestCase):
 def fixture(self,root):
  (root/'a.txt').write_text('fixture')
  files={'a.txt':hashlib.sha256(b'fixture').hexdigest()}
  (root/'UPLOAD_ALLOWLIST.json').write_text(json.dumps({'files':files,'payload_sha256':payload(files)}))
 def test_exact(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.fixture(p);self.assertEqual(verify(p)['files'],2)
 def test_missing(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.fixture(p);(p/'a.txt').unlink()
   with self.assertRaisesRegex(ValueError,'FILE_SET'):verify(p)
 def test_unexpected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.fixture(p);(p/'.env').write_text('synthetic test only')
   with self.assertRaisesRegex(ValueError,'FILE_SET'):verify(p)
 def test_modified(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.fixture(p);(p/'a.txt').write_text('changed')
   with self.assertRaisesRegex(ValueError,'CONTENT'):verify(p)
 def test_payload(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.fixture(p);f=p/'UPLOAD_ALLOWLIST.json';x=json.loads(f.read_text());x['payload_sha256']='0'*64;f.write_text(json.dumps(x))
   with self.assertRaisesRegex(ValueError,'PAYLOAD'):verify(p)
 def test_symlink(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.fixture(p);(p/'a.txt').unlink();(p/'a.txt').symlink_to('UPLOAD_ALLOWLIST.json')
   with self.assertRaisesRegex(ValueError,'INVALID'):verify(p)
