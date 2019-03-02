import unittest
import json
import pprint
from zenki import Setup, Zenki, Downloader, Console

class TestSetup:
  @classmethod
  def removePackages(self):
    import subprocess, sys
    required_modules = [('requests', 'requests'), ('mastodon.py', 'mastodon')]
    for package, module in required_modules:
      subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y",
                       package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  
  
class ZenkiASetupTest(unittest.TestCase):
  def setUp(self):
    Console.testMode = True
    TestSetup.removePackages()
    with open('config.test.json') as f:
      self.config = json.loads(f.read())
      self.config['CreateClientSecret'] = False
  
  def test_setup(self):
    pprint.pprint(self.config)
    self.assertEqual(Setup.setup(**self.config), 'OK', 'Setup install Failed')
    import mastodon, requests
    self.assertEqual(mastodon.__name__, 'mastodon', 'Mastodon not installed correctly.')
    self.assertEqual(requests.__name__, 'requests', 'Requests not installed correctly.')


class ZenkiBClientTest(unittest.TestCase):
  def setUp(self):
    Console.testMode = True
    with open('config.test.json') as f:
      self.testConfig = json.loads(f.read())
      self.testConfig.pop('password')
    self.ZenkiInstance = Zenki.loadInstanceFromConfig()

  def test_Acreate_client(self):
    self.assertEqual(self.ZenkiInstance.config, self.testConfig)
  
  def test_Bdownload_post(self):
    post_id = 101682564527694969
    post = self.ZenkiInstance.mclient.status(post_id)
    self.ZenkiInstance.downloader.downloadMediaStatus(post)

  def test_Cdownload_multi_post(self):
    post_id = 100493658352114533
    post = self.ZenkiInstance.mclient.status(post_id)
    self.ZenkiInstance.downloader.downloadMediaStatus(post)


if __name__ == '__main__':
    unittest.main()
