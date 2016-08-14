from setuptools import setup


setup(name='heos',
      version=open('heos/version.py').read(),
      description='Denon Heos',
      url='http://github.com/andryd/heos',
      author='Andreas Rydbrink',
      author_email='andreas.rydbrink@gmail.com',
      license='MIT',
      packages=['heos'],
      long_description=open('README.md').read(),
      install_requires=[],
      zip_safe=False)
