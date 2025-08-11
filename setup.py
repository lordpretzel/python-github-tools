from setuptools import setup

package = 'github-tools'
version = '1.0'
requirements = [
          'ghapi',
          'requests'
      ]
setup(name=package,
      version=version,
      description="Tools for github API scripting",
      install_requires=requirements,
      packages = [ 'github_tools' ],
      entry_points={
          'console_scripts': [
              'github-tools = github_tools.github_tools:main',
          ],
      },
      url='url')
