import sys, os, shutil, json, threading, queue
import pprint
LOG_LEVEL = 0

class Console():
  """
    Log Level Codes
      0 = Verbose
      1 = Errors
      2 = Log
      3 = None
  """
  testMode = False

  @classmethod
  def log(self, *args, **kwargs):
    if LOG_LEVEL <= 2:
      print('[LOG]', *args, **kwargs)
  
  @classmethod
  def ok(self, *args, **kwargs):
    if LOG_LEVEL <= 2:
      print('[OK]', *args, **kwargs)

  @classmethod
  def error(self, *args, **kwargs):
    if LOG_LEVEL <= 1:
      print('[ERR]', *args, **kwargs)

  @classmethod
  def warn(self, *args, **kwargs):
    if LOG_LEVEL <= 2:
      print('[!!]', *args, **kwargs)

  @classmethod
  def testlog(self, *args, **kwargs):
    if self.testMode:
      print('[TEST]', *args, **kwargs)

class Setup():
  
  @classmethod
  def setup(self, **custom):
    self.printLogo()
    Console.log('No configuration found, running setup.')
    Console.log('---- Initial Stuff ----')
    Console.log('/!\\ run "zenki.py setup" to run the setup again.')
    Console.log(' Or just edit config.json.')
    # Check python version this is running on
    assert sys.version_info > (3, 5), 'You need Python 3.5 or greater to run this program.'
    Console.ok('Python Version')
    Console.warn('Verifying needed modules...')
    self.checkAndInstallRequirements()
    self.createCredentials(custom)
    return 'OK'

  @classmethod
  def createCredentials(self, custom={}):
    _base_url, _email, _password =  "", "", ""
    if 'base_url' not in custom:
      _base_url = input("Instance URL ('https://pawoo.net'): ")
      _email = input("Email: ")
      _password = input("Password (visible): ")
    
    config = {
      'base_url': custom.get('base_url', _base_url),
      'app_secret': custom.get('app_secret', 'zenki.app.secret'),
      'user_secret': custom.get('user_secret', 'zenki.user.secret'),
      'email': custom.get('email', _email),
      'password': custom.get('password', _password),
      'download': {
          'save_path': custom.get('save_path', './'),
          'folder_if_multiple': custom.get('folder_if_multiple', True),
          'folder_per_user': custom.get('folder_per_user', True),
          'user_folder_format': custom.get('user_folder_format', '{account.id}-{account.acct}'),
          'media_filename_format': custom.get('media_filename_format', '{media.id}-{raw}.{extension}'),
          'queue_size': custom.get('queue_size', 10),
          'worker_size': custom.get('worker_size', 5),
          'overwrite_existing': custon.get('overwrite_existing', False)
      }
    }

    from mastodon import Mastodon

    if custom.get('CreateClientSecret', True):
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
    with open(custom.get('configpath', 'config.json'), 'w') as f:
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


class DownloadWorker(threading.Thread):

  def __init__(self, workerIndex, r, workQueue):
    threading.Thread.__init__(self)
    self.daemon = True
    self.index = workerIndex
    self.queue = workQueue
    self.r = r

  def run(self):
    while True:
      url, path = self.queue.get()
      Console.log('[ZenkiWorker-{index}] Saving: {url}'.format(index=self.index, url=url))
      response = self.r.get(url, stream=True)
      with open(path, 'wb') as out_file:
          shutil.copyfileobj(response.raw, out_file)
      del response
      self.queue.task_done()


class Downloader():

  def __init__(self, config):
    import requests
    self.r = requests
    self.queue = queue.Queue(config.get('queue_size', 10))
    self.__dict__.update({
      'save_path'         : config.get('save_path', './'),
      'folder_if_multiple': config.get('folder_if_multiple', True),
      'folder_per_user'   : config.get('folder_per_user', True),
      'user_folder_format': config.get('user_folder_format', '{account.id}-{account.acct}'),
      'media_filename_format': config.get('media_filename_format', '{media.id}-{raw}.{extension}'),
      'overwrite_existing': config.get('overwrite_existing', False)
    })

    self.workers = [DownloadWorker(x, self.r, self.queue)
                    for x in range(config.get('worker_size', 5))]
    for i in self.workers:
      i.start()
  

  def createPath(self, post):
    final_path = [self.save_path]
    if self.folder_per_user:
      final_path.append(self.user_folder_format.format(account=post.account))
    if self.folder_if_multiple and len(post.media_attachments) > 1:
      final_path.append(str(post.id))

    Console.testlog(final_path)
    directory = os.path.join(*final_path)
    os.makedirs(directory, exist_ok=True)
    return final_path


  def downloadMediaStatus(self, post):
    for media in post.media_attachments:
      path = self.createPath(post)
      url_filename = media.url.split('/')[-1]
      raw_filename = ".".join(url_filename.split('.')[:-1])
      extension = media.url.split('.')[-1]
      filename = self.media_filename_format.format(media=media, raw=raw_filename, extension=extension)
      path.append(filename)
      file_path = os.path.join(*path)
      
      if os.path.exists(file_path) and not self.overwrite_existing:
        Console.log('Skipping:', file_path)
        continue

      Console.testlog('Saving To: ', file_path)
      self.queue.put((media.url, file_path))
      # response = self.r.get(media.url, stream=True)
      # with open(file_path, 'wb') as out_file:
      #     shutil.copyfileobj(response.raw, out_file)
      # del response
    
    return 'OK'

    

class Zenki():
  
  @classmethod
  def loadInstanceFromConfig(self, configJson='config.json'):
    Console.log('Loading From Json: ', configJson)
    import json
    #try:
    with open(configJson) as f:
      config = json.loads(f.read())
      return Zenki(**config)
    #except Exception as e:
    #  Console.error('Loading Json Failed: ', e)


  def __init__(self, **config):
    from mastodon import Mastodon
    self.config = config
    self.downloader = Downloader(config['download'])
    self.mclient = Mastodon(
      access_token=config['user_secret'],
      client_secret=config['app_secret'],
      api_base_url=config['base_url']
    )
    self.resolved_users = {}

  def resolveUserId(self, username):
    if username == int:
      return username
    if username not in self.resolved_users:
      result = self.mclient.account_search(username)
      if result:
        self.resolved_users[username] = result[0]
      else:
        try:
          return int(username)
        except:
          pass
        raise NoUserFound(username)
    
    return self.resolved_users[username].id


  def downloadTimelineImages(self, username):
    userId = self.resolveUserId(username)
    Console.log('Downloading Timeline:', userId)
    timeline = self.mclient.account_statuses(userId, only_media=True)
    while timeline:
      for status in timeline:
        Console.log('Queueing', status.id)
        self.downloader.downloadMediaStatus(status)
      timeline = self.mclient.fetch_next(timeline)
    Console.log('Waiting for the remaining downloads to finish.')
    self.downloader.queue.join()


  def downloadFollowing(self, username):
    # self.mclient.account_verify_credentials()
    userId = self.resolveUserId(username)
    following = self.mclient.account_following(userId)
    while following:
      for account in following:
        Console.log('Fetching Following', account.id, account.username)
        self.downloadTimelineImages(account.id)
      following = self.mclient.fetch_next(following)


class NoUserFound(Exception):
  pass

def printHelp():
  Setup.printLogo()
  Console.log("\n".join([
    '-- Mastodon Download Tool --',
    'Note: "user" may refer to the mastodon username(@nokusu, nokusu, @nokusu@pawoo.net) or ID(123567).\n',
    'Usage:',
    ' Setup',
    ' -> Run the initial setup process, mastodon requires an account to get full',
    '    access to the required API features.\n',
    ' DownloadUserTimeline {user}',
    ' -> Downloads the media timeline of the specified user.\n',
    ' DownloadFollowingTimeline {user}',
    ' -> Downloads the timelines of the accounts the specified user is following.',
    ]))

def loadZenki(config_path):
    if not os.path.exists(config_path):
      Setup.setup(configpath=config_path)
    return Zenki.loadInstanceFromConfig(config_path)

if __name__ == "__main__":
  config_path = os.path.join(os.path.dirname(sys.argv[0]), 'config.json')
  arguments = sys.argv[1:]
  if not arguments:
    noargs_file = os.path.join(os.path.dirname(sys.argv[0]), 'noargs')
    if os.path.exists(noargs_file):
      with open(noargs_file) as f:
        Console.log('Running from noargs file')
        arguments.extend(f.read().split(' '))
    else:
      printHelp()

  op = arguments.pop(0)

  if op.lower() == 'help':
    printHelp()
  
  elif op == 'Setup':
    Setup.setup(configpath=config_path)

  elif op == 'DownloadUserTimeline':
    username = arguments.pop(0)
    loadZenki(config_path).downloadTimelineImages(username)

  elif op == 'DownloadFollowingTimeline':
    username = arguments.pop(0)
    loadZenki(config_path).downloadFollowing(username)
