from setuptools import setup, find_packages


setup(name='findcrypt3',
      version="0.1",
      packages=find_packages(exclude=['ez_setup']),
      install_requires=["yara-python"],
      include_package_data=True,
      entry_points={
          "idapython_plugins": [
              "findcrypt3=findcrypt3.findcrypt3:Findcrypt_Plugin_t",
          ]
      })
