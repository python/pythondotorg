import os
import invoke

BASE_DIR = os.path.dirname(__file__)

env = {
    'host': 'virt-l4es2w.psf.osuosl.org',
    'python': '/srv/redesign.python.org/shared/env/bin/python',
    'deploydir': '/srv/redesign.python.org/current',
}


def run(cmd, **kwargs):
    """
    Wrapper around invoke.run to automatically interpolate env.
    """
    return invoke.run(cmd.format(**dict(env, **kwargs)))


@invoke.task
def chef():
    run('ssh {host} sudo chef-client')


@invoke.task
def django(c):
    run('ssh {host} sudo {python} {deploydir}/manage.py {c} --settings pydotorg.settings.staging', c=c)


@invoke.task
def copy_data_from_staging(keep=False):
    run('curl -s -o staging.json https://preview.python.org/__secret/devfixture/')
    run('python manage.py loaddata staging.json')
    if not keep:
        run('rm -f staging.json')


@invoke.task
def clear_pycs():
    """ Remove all .pyc files from project directory """
    run("""find {} -name "*.pyc" -delete""".format(BASE_DIR))
