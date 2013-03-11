import invoke

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
