#!/usr/bin/python
'''Produce a makefile for compiling the source code for a specified target/configuration.
The resultant makefile requires makedepf90 (http://personal.inet.fi/private/erikedelmann/makedepf90/)
to produce a list of dependencies.

Usage:
    ./mkconfig.py [options] configuration

where [options] are:
    -h,--help   Print this message and exit.
    -c,--config Print out the available configurations and their settings.
    -d,--debug  Turn on debug flags (and turn off all optimisations).
'''

import os,pprint,sys

class makefile_flags(dict):
    '''Initialise dictionary with all makefile variables not given set to be empty.

    Usage: makefile_flags(FC='ifort',FFLAGS='-O3') creates a dictionary of the 
    makefile flags and sets FC and FFLAGS, with all other flags existing but set to 
    be empty.'''
    def __init__(self,**kwargs):
        dict.__init__(self,FC='',
                           FFLAGS='',
                           CPPDEFS='',
                           CPPFLAGS='',
                           LD='',
                           LDFLAGS='',
                           LIBS='',
                           MODULE_FLAG='',) # Flag compiler uses for setting the directory 
                                            # in which to place/search for .mod files.
                                            # Must be followed by $(DEST).  This is to 
                                            # accommodate the compilers which want a space
                                            # after the flag as well as those that don't!
                                            # e.g. for g95 MODULE_FLAG='-fmod=$(DEST)' 
                                            # whilst for gfortran MODULE_FLAG='-M $(DEST)'.
        self.update(**kwargs)

#======================================================================
# Local settings.

program_name='bin/hubbard.x'

# Space separated list of files to be compiled in a format understood by bash to pass to
# makedepf90.  Patterns are allowed, but all patterns must match at least one file, as 
# otherwise makedepf90 complains, throws an error and exits.
source_code_files='src/*.f90 lib/*.{f90,F90}'

#======================================================================
# Edit this section to add new configurations.

ifort=makefile_flags(
          FC='ifort',
          FFLAGS='',
          LD='ifort',
          MODULE_FLAG='-module $(DEST)'
      )

# Use makefile_flags(**ifort) rather than just =ifort so that 
# ifort_mpi has the makefile_flags class, rather than being a normal
# dict. This enables us to search for all created configurations automatically.
# The same can be achieved using ifort_mpi=copy.copy(ifort), but I chose not to.
ifort_mpi=makefile_flags(**ifort) # Initialise with the same settings as the serial platform.
ifort_mpi.update(                 # Now change only the settings we want to...
          FC='mpif90',
          LD='mpif90',
          CPPDEFS='-D__PARALLEL'
      )

gfortran=makefile_flags(
          FC='gfortran',
          FFLAGS='-O3 -fbounds-check',
          LD='gfortran',
          MODULE_FLAG='-M $(DEST)',
      )

gfortran_mpi=makefile_flags(**gfortran)
gfortran_mpi.update(
          FC='mpif90',
          FFLAGS='-I /usr/local/shared/suse-10.3/x86_64/openmpi-1.2.6-gnu/lib',
          LD='mpif90',
          CPPDEFS='-D__PARALLEL'
      )

g95=makefile_flags(
          FC='g95',
          FFLAGS='-fbounds-check',
          LD='g95',
          MODULE_FLAG='-fmod=$(DEST)',
      )

nag=makefile_flags(
          FC='nagfor',
          CPPFLAGS='-DNAGF95',
          LD='nagfor',
          MODULE_FLAG='-mdir $(DEST)',
      )

pgf90=makefile_flags(
          FC='pgf90',
          FFLAGS='-O3 -Mbounds',
          LD='pgf90',
          MODULE_FLAG='-module $(DEST)'
      )

pgf90_mpi=makefile_flags(**pgf90)
pgf90_mpi.update(
          FC='mpif90',
          LD='mpif90',
          CPPDEFS='-D__PARALLEL'
      )

pathf95=makefile_flags(
          FC='pathf95',
          FFLAGS='',
          LD='pathf95',
          MODULE_FLAG='-module $(DEST)'
      )

#======================================================================

# Get list of possible platforms.
configurations={}
for name,value in locals().items():
    if value.__class__==makefile_flags().__class__:
        configurations[name]=value

makefile_template='''#Generated by mkconfig.py.

SHELL=/bin/bash # For our sanity!

# Get the version control id.  Works with either svn or git or if no VCS is used.
# Outputs a string.
VCS_VER:=$(shell set -o pipefail && echo -n \\" && ( git log --max-count=1 --pretty=format:%%H || echo -n 'Not under version control.' ) 2> /dev/null | tr -d '\\r\\n'  && echo -n \\")

# Test to see if the working directory contains changes. Works with either svn or git.
# If the working directory contains changes (or is not under version control) then
# the _WORKING_DIR_CHANGES flag is set.
WORKING_DIR_CHANGES := $(shell git diff --quiet --cached && git diff --quiet 2> /dev/null || echo -n "-D_WORKING_DIR_CHANGES")

FC=%(FC)s
FFLAGS=-I $(DEST) %(FFLAGS)s

CPPDEFS=%(CPPDEFS)s -D_VCS_VER='$(VCS_VER)'
CPPFLAGS=%(CPPFLAGS)s $(WORKING_DIR_CHANGES)

LD=%(LD)s
LDFLAGS=%(LDFLAGS)s
LIBS=%(LIBS)s

SRC=${PWD}
DEST=$(SRC)/dest

# We put compiled objects and modules in $(DEST).  If it doesn't exists, create it.
make_dest:=$(shell	test -e $(DEST) || mkdir -p $(DEST))

# LINK_LINE is passed through to makedepf90.  It is necessary to escape the variable from
# both make (hence $$) and from the shell (hence \$$) to keep the variables from being
# expanded in the .depend file.
# Note the recursive make: this is so that compilation of the environment report is forced
# if any other files are compiled.
LINK_LINE="\$$(MAKE) \$$(DEST)/environment_report.o FORCE=frc_rebuild ;\$$(FC) -o \$$@ \$$(FFLAGS) \$$(LDFLAGS) -I \$$(DEST) \$$(FOBJ) \$$(LIBS)" 

.SUFFIXES:
.SUFFIXES: .f90 .F90

$(DEST)/%%.o: */%%.f90
\t$(FC) -c $(FFLAGS) $< -o $@ %(MODULE_FLAG)s

$(DEST)/%%.o: */%%.F90
\t$(FC) $(CPPDEFS) $(CPPFLAGS) -c $(FFLAGS) $< -o $@ %(MODULE_FLAG)s

include .depend

docs:
\tcd documentation && $(MAKE) html pdf soft_links

clean: 
\t-rm -f {$(DEST)/,bin/}{*.mod,*.o,*.x}

# Build from scratch.
new: clean %(PROGRAM)s

# Dummy target.  Used to force rebuilds.
frc_rebuild: ;

# Set all files to depend upon the FORCE variable.  If FORCE is set to frc_build, then all object
# files are built (even if not necessary).
# sed is used for prettier output, as makedepf90 won't let us have multiple lines in the link statement.
depend .depend:
\tmakedepf90 -o %(PROGRAM)s -b "\$$(DEST)" -l $(LINK_LINE) %(SOURCE_CODE)s -d "\$$(FORCE)" | sed -e 's/;/\\n\\t/' > .depend

help:
\t@echo "Please use \`make <target>' where <target> is one of:"
\t@echo "  %(PROGRAM)-20s [default target] Compile program."
\t@echo "  clean                Remove the compiled objects."
\t@echo "  new                  Remove all previously compiled objects and re-compile."
\t@echo "  depend               Produce the .depend file containing the dependencies."
\t@echo "                       Requires the makedepf90 tool to be installed."
\t@echo "  docs                 Build documents in pdf and html formats."
\t@echo "                       Requires Sphinx to be installed."
\t@echo "  help                 Print this help message."
'''

def create_makefile(config,debug=False):
    '''Create the Makefile for the desired config.  If debug is True, then the FFLAGS and LDFLAGS of the configuration are overwritten with the -g debug flag.'''
    if debug: config.update(FFLAGS='-g',LDFLAGS='-g')
    config.update(PROGRAM=program_name,SOURCE_CODE=source_code_files)
    f=open('Makefile','w')
    f.write(makefile_template % config)
    f.close()

if __name__=='__main__':
    args=sys.argv[1:]
    if '-d' in args or '--debug' in args:
        debug=True
        args=[arg for arg in args if (arg!='-d' and arg!='--debug')]
    else:
        debug=False
    if '-c' in args or '--config' in args:
        print 'Available configurations are:'
        for k,v in sorted(configurations.items()):
            print '\n%s' % k
            pprint.pprint(v)
        sys.exit()
    if '-h' in args or '--help' in args or len(args)!=1:
        print '%s\nAvailable configurations are: %s.' % (__doc__,', '.join(sorted(configurations.keys())))
        sys.exit()
    try:
        config=configurations[args[0]]
    except KeyError:
        print 'Configuration not recognized: %s' % args[0]
        print 'Available configurations are: %s.' % (', '.join(sorted(configurations.keys())))
        sys.exit()
    create_makefile(config,debug)