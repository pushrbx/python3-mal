try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup


long_description = open('README.markdown').read()


config = {
  'name': 'python3-mal',
  'description': 'Provides programmatic access to MyAnimeList resources.',
  'author': 'pushrbx',
  'keywords': ['myanimelist', 'mal-api', 'mal python', 'myanimelist python', 'python3-mal', 'myanimelist api'],
  'python_requires': '>=3.4, <4',
  'license': 'LICENSE.txt',
  'long_description': long_description,
  'long_description_content_type': 'text/markdown',
  'url': 'https://github.com/pushrbx/python3-mal',
  'download_url': 'https://github.com/pushrbx/python3-mal/archive/master.zip',
  'author_email': 'contact@pushrbx.net',
  'version': '0.2.20',
  'install_requires': ['urllib3>=1.21.1,<1.23', 'requests<=2.18.4', 'pytz', 'lxml==4.3.4', 'cssselect'],
  'tests_require': ['nose'],
  'packages': ['myanimelist']
}

setup(**config)
