.. _restart_table:

restart options
===============

The ``restart`` table contains options relating to checkpointing within QMC calculations.

HANDE currently uses one restart file per MPI rank with a filename of the form
``HANDE.RS.X.pY.H5``, where ``X`` is the restart index and ``Y`` is the MPI rank.

``read``
    type: boolean or integer.

    Optional.  Default: false.

    Start a QMC calculation from a previous calculation if ``true`` or an integer.  If
    ``true``, then the highest value of ``X`` is used for which a set of restart files
    exists, otherwise specifies the value of ``X`` to use.

    .. note::

        The calculation should be the same as the one that produced the ouput file, but it
        is possible to restart a calculation using an enlarged basis.  The orbitals of the
        old (small) basis must correspond to the first orbitals of the new (larger) basis.
``write``
    type: boolean or integer.

    Optional.  Default: false.

    Write out checkpointing files at the end of the calculation if ``true`` or an
    integer.  If ``true``, then the highest value of ``X`` is used for which a set of
    restart files doesn't exist, otherwise specifies the value of ``X`` to use.
``write_shift``
    type: boolean or integer.

    Optional.  Default: false.

    Write out checkpointing files when the shift is allowed to vary (i.e. once
    ``target_population`` is reached) if ``true`` or an integer.  If ``true``, then the
    highest value of ``X`` is used for which a set of restart files doesn't exist,
    otherwise specifies the value of ``X`` to use.
``write_frequency``
    type: integer.

    Optional.  Default: :math:`2^{31}-1`.

    Write out checkpointing files every `N` report loops, where `N` is the
    specified value.

    .. note::

        The index used for the restart files created with this option is the next
        unused index.  Depending upon the frequency used, a large number of restart files
        may be created.  As such, this option is typically only relevant for debugging or
        explicitly examining the evolution of the stochastic representation of the
        wavefunction.
``rng``
    type: boolean

    Optional. Default: true.

    Restart the state of the DSFMT random number generator from the previous calculation,
    allowing restarted calculations to follow the same Markov chain as if the entire
    series of calculations had been performed as a single calculation.

    .. note::

        #. Calculations using OpenMP threads will not follow the same Markov chain due to
           the non-deterministic load balancing behaviour of the OpenMP implementation.
        #. Restart files from older restart files do not contain the necessary information
           to recreate the RNG state. This option is ignored automatically in such cases.
        #. Due to each processor using its own RNG stream, this functionality can only be
           used when restarting calculations on the same number of processors.
           Restart files created by the ``redistribute`` function will not contain RNG
           information as a result. This option is automatically ignored in such cases.
        #. The presence of the RNG information in a restart file can be detected by
           running the command

           .. code-block:: bash

               $ h5dump -A -d rng/state <restart file>

           where ``<restart file>`` is the appropriate filename, which will return some
           metadata information on the ``rng/state`` dataset if the RNG state is present
           and an error otherwise.

