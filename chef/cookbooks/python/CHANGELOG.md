python Cookbook CHANGELOG
=========================
This file is used to list changes made in each version of the python cookbook.


v1.4.4
------
[COOK-3816] - Including ez_setup script with cookbook instead of downloading from the internet


v1.4.2
------
### Bug
- **[COOK-3796](https://tickets.opscode.com/browse/COOK-3796)** - Virtualenv can fail

### Improvement
- **[COOK-3719](https://tickets.opscode.com/browse/COOK-3719)** - Allow alternative install python, update pip location
- **[COOK-3703](https://tickets.opscode.com/browse/COOK-3703)** - Create symlink for source built python [python3 support]


v1.4.0
------
### New Feature
- **[COOK-3248](https://tickets.opscode.com/browse/COOK-3248)** - Improve testing suite

### Improvement
- **[COOK-3125](https://tickets.opscode.com/browse/COOK-3125)** - Don't use `normal` attributes

### Bug
- **[COOK-3084](https://tickets.opscode.com/browse/COOK-3084)** - Fix `python_virtualenv` on EL 5

v1.3.6
------
### Bug
- [COOK-3305]: distribute merged back into setuptools

### New Feature
- [COOK-3248]: Improve testing suite in the python cookbook

v1.3.4
------
### Bug
- [COOK-3137]: `python_pip` LWRP cannot have differnent name and `package_name`

v1.3.2
------
### Bug
- [COOK-2917]: python::source fails on CentOS 6.3 minimal (make: command not found)
- [COOK-3077]: Python - pip fails to install when `['python']['install_method'] == 'source'`

v1.3.0
------
### Bug
- [COOK-2376]: Python pip default action
- [COOK-2468]: python cookbook - Chef 11 compat fixes
- [COOK-2882]: Python source recipe fails on Ubuntu 12.10 because of unavailable libdb4.8-dev package
- [COOK-3009]: fix build time dependencies and gcc flags for python source on newer ubuntus

### New Feature
- [COOK-2449]: Make the distribute download location an attribute
- [COOK-3008]: Update python::source to install 2.7.5

### Sub-task
- [COOK-2866]: python::source checks existence of a directory that already exists

v1.2.2
------
- [COOK-2297] - more gracefully handle pip packages from VCS and source archives

v1.2.0
------
- [COOK-1866] - /usr/bin is not a pip binary location in source installs on RHEL
- [COOK-1925] - add smartos support

v1.1.0
------
- [COOK-1715] - Add user and group to python_pip
- [COOK-1727] - Python cookbook cannot install `pip` on CentOS versions < 6

v1.0.8
------
- [COOK-1016] - python package needs separate names for centos/rhel 5.x vs 6.x
- [COOK-1048] - installation of pip does not honor selected python version
- [COOK-1282] - catch Chef::Exceptions::ShellCommandFailed for chef 0.10.8 compatibility
- [COOK-1311] - virtualenv should have options attribute
- [COOK-1320] - pip provider doesn't catch correct exception
- [COOK-1415] - use plain 'python' binary instead of versioned one for default interpreter

v1.0.6
------
- [COOK-1036] - correctly grep for python-module version
- [COOK-1046] - run pip inside the virtualenv

v1.0.4
------
- [COOK-960] - add timeout to python_pip
- [COOK-651] - 'install_path' not correctly resolved when using python::source
- [COOK-650] - Add ability to specify version when installing distribute.
- [COOK-553] - FreeBSD support in the python cookbook
