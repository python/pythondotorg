from pipeline.compilers import sass


class DummySASSCompiler(sass.SASSCompiler):

    def compile_file(self, infile, outfile, outdated=False, force=False):
        pass
