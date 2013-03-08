from invoke import run, task

@task
def chef():
    run('ssh virt-l4es2w.psf.osuosl.org sudo chef-client')
