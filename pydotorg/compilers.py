"""Custom asset compilers for the Django pipeline."""

from pipeline.compilers import sass


class DummySASSCompiler(sass.SASSCompiler):
    """No-op SASS compiler for development without a SASS binary."""

    def compile_file(self, infile, outfile, outdated=False, force=False):
        """Skip compilation entirely."""
