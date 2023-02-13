Package structure
=================

.. code-block:: python

   eurocodepy
      db
      ec1
         snow
         wind
            pressure
      ec2
         sls
            longterm
            deforrmation
            crack
         uls
            bend_simple
            shear
            punch
            torsion
         fire
            fire_base
      ec5
         sls
         uls
      ec8

Basic functions
===============

A set of functions to get material properties. Properties are stored in .json file. 

.. automodule:: db
   :members:

Eurocodes 0 and 1
=================

.. automodule:: ec1.wind.pressure
   :members:

Eurocode 2
==========

.. automodule:: ec2.sls.longterm
   :members:

.. automodule:: ec2.sls.crack
   :members:

.. automodule:: ec2.uls.shear
   :members:

.. automodule:: ec2.uls.bend_beam
   :members:

.. automodule:: ec2.uls.bend_shell
   :members:

Eurocode 5
==========

.. automodule:: ec5.uls.bend
   :members:

.. automodule:: ec5.uls.shear
   :members:

Eurocode 8
==========

.. automodule:: ec8.spetrum
   :members:

Utils
=====

.. automodule:: utils.stress
   :members: