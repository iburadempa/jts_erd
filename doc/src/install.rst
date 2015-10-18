Installation
============

Install graphviz and build tools::

  aptitude install pkg-config build-essential graphviz libgraphviz-dev

You will need at least PyGraphviz 1.3.1 when using python3.

Currently (as of version 1.3.1 of pygraphviz) on at least debian and ubuntu you need special install options due to a bug (https://github.com/pygraphviz/pygraphviz/issues/71)::

  pip3 install pygraphviz --install-option="--include-path=/usr/include/graphviz" --install-option="--library-path=/usr/lib/graphviz/"

(gcc still throws a warning.)

Prepare a virtualenv with python3::

  mkdir jts_erd
  cd jts_erd
  virtualenv -p python3
  source bin/activate

In the virtualenv root dir::

  git clone https://github.com/iburadempa/jts_erd.git

