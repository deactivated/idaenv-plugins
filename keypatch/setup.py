from setuptools import setup, find_packages


setup(name='keypatch',
      version="0.0",
      packages=find_packages(exclude=['ez_setup']),
      install_requires=[
          "keystone-engine"
      ],
      zip_safe=False,
      entry_points={
          "idapython_plugins": [
              "keypatch=keypatch:Keypatch_Plugin_t",
          ]
      })
