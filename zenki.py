import sys

LOG_LEVEL = 0

class Console():
  """
    Log Level Codes
      0 = Verbose
      1 = Errors
      2 = Log
      3 = None
  """
  @classmethod
  def log(self, *args, **kwargs):
    if LOG_LEVEL <= 2:
      print(*args, **kwargs)
  
  @classmethod
  def ok(self, *args, **kwargs):
    if LOG_LEVEL <= 2:
      print('[OK]', *args, **kwargs)

  @classmethod
  def error(self, *args, **kwargs):
    if LOG_LEVEL <= 1:
      print('[Er]', *args, **kwargs)

  @classmethod
  def warn(self, *args, **kwargs):
    if LOG_LEVEL <= 2:
      print('[!!]', *args, **kwargs)


class Setup():
  
  @classmethod
  def setup(self):
    self.printLogo()
    Console.log('No configuration found, running setup.')
    Console.log('---- Inital Stuff ----')
    # Check python version this is running on
    assert sys.version_info > (3, 5), 'You need Python 3.5 or greater to run this program.'
    Console.ok('Python Version')
    Console.warn('Verifying needed modules...')
    self.checkAndInstallRequirements()
    self.createCredentials()
    return 0

  @classmethod
  def createCredentials(self, custom={}):
    import json
    config = {
      'base_url': custom.get('api_base_url', input("Instance URL ('https://pawoo.net'): ")),
      'app_secret': custom.get('app_secret', 'zenki.app.secret'),
      'user_secret': custom.get('user_secret', 'zenki.user.secret'),
      'email': custom.get('email', input("Email: ")),
      'password': custom.get('password', input("Password (visible): ")),
    }

    from mastodon import Mastodon
    Console.log('Creating Client Secret...')
    Mastodon.create_app('zenki',
      api_base_url=config['base_url'],
      to_file = config['app_secret']
    )
    mastodon = Mastodon(
        client_id=config['app_secret'],
        api_base_url=config['base_url'],
    )
    Console.log('Creating User Secret...')
    mastodon.log_in(
        config['email'],
        config['password'],
        to_file=config['user_secret']
    )
    config.pop('password')
    Console.log('Writing Config...')
    with open('config.json', 'w') as f:
      f.write(json.dumps(config, indent=4))
    Console.ok('Credential Setup Done!')


  @classmethod
  def printLogo(self):
    print("""  _____          _    _ 
 |__  /___ _ __ | | _(_)
   / // _ \ '_ \| |/ / |
  / /|  __/ | | |   <| |
 /____\___|_| |_|_|\_\_|""")

  @classmethod
  def checkAndInstallRequirements(self):
    import subprocess, sys
    import importlib
    required_modules = [('requests', 'requests'), ('mastodon.py', 'mastodon')]
    for package, module in required_modules:
      try:
        importlib.import_module(module)
        Console.ok('Module:', module, package)
      except:
        Console.warn('Module:', module, package, 'not found. Installing...')
        subprocess.call([sys.executable, "-m", "pip", "install", package],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Console.log('Module:', module, package, 'installed.')


