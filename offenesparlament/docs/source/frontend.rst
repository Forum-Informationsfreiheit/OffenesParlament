Frontend
========

This section describes the frontend code and how to build it

Tech
~~~~~~~~~~

* `React <https://facebook.github.io/react/>`_
* `VisualSearch <https://documentcloud.github.io/visualsearch/>`_


Building
~~~~~~~~

We use grunt to build our frontend code. It is generated from the sources in ``client/`` and is output to ``offenesparlament/offenesparlament/static/``.

We commit all generated files to git.

Grunt is already installed in the vagrant VM, so you should be able to run the
build task from the VM right away in the dir ``/vagrant``::

  grunt dev

This task watches all source files and rebuilds if necessary.

To use BrowserSync and have the browser reload every time frontend files change, run::

  grunt reloading

Grunt too slow?
---------------

If grunt is too slow running inside the VM (Probably due to file-watching on the host system)
you'll have to install the following on your computer:

* `Node.js and npm <https://docs.npmjs.com/getting-started/installing-node>`_ (Make sure you run recent versions of both)
* `grunt-CLI <https://github.com/gruntjs/grunt-cli>`_
* `Sass <http://sass-lang.com/install>`_ (You might need to install Ruby first)

Then you can run grunt tasks on your computer from the project dir ``OffenesParlament`` (where the ``Gruntfile.coffee`` is located)
