0template
=========

Copyright 2015 Thomas Leonard et al


Introduction
------------

0template is a tool for creating [Zero Install](http://0install.net/) feeds from template files.
It is mainly used to add new releases to feeds managed by [0repo](http://0install.net/0repo.html).

To make the `0template` command available on your command-line you can run:

    0install add 0template http://0install.net/tools/0template.xml

To create a new template file you can then use a command like the following:

    0template my-app.xml.template

To generate a template file from an existing feed using simple heuristics instead use:

    0template my-app.xml.template --from-feed=my-app.xml

Once you have a template file you can pass in values for variables defined in the template:

    0template my-app.xml.template version=1.0

This will cause 0template to create a new file named `my-app-1.0.xml` with any occurences of `{version}` substituted with `1.0` and `<manifest-digest>`s calculated.

For additional documentation please see: http://0install.net/0template.html


Conditions
----------

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
