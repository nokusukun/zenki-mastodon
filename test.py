import unittest

from zenki import Setup

class TestSetup:
  @classmethod
  def removePackages(self):
    import subprocess, sys
    required_modules = [('requests', 'requests'), ('mastodon.py', 'mastodon')]
    for package, module in required_modules:
      subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y",
                       package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  
class ZenkiSetupTest(unittest.TestCase):
  def setUp(self):
    TestSetup.removePackages()
  
  def test_setup(self):
    self.assertEqual(Setup.setup(), 0, 'Setup install Failed')
    import mastodon, requests
    self.assertEqual(mastodon.__name__, 'mastodon', 'Mastodon not installed correctly.')
    self.assertEqual(requests.__name__, 'requests', 'Requests not installed correctly.')

  def tearDown(self):
    TestSetup.removePackages()


if __name__ == '__main__':
    unittest.main()
