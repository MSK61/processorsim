# -*- coding: utf-8 -*-

"""rope configuration"""

############################################################
#
# Copyright 2017, 2019, 2020, 2021, 2022, 2023 Mohammed El-Afifi
# This file is part of processorSim.
#
# processorSim is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# processorSim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with processorSim.  If not, see
# <http://www.gnu.org/licenses/>.
#
# program:      processor simulator
#
# file:         config.py
#
# function:     rope project configuration
#
# description:  rope configuration settings
#
# author:       Mohammed El-Afifi (ME)
#
# environment:  Visual Studio Code 1.74.2, python 3.11.1, Fedora release
#               37 (Thirty Seven)
#
# notes:        This is a private program.
#
############################################################
# The default ``config.py``
# flake8: noqa


def set_prefs(prefs):
    """This function is called before opening the project"""

    # Specify which files and folders to ignore in the project.
    # Changes to ignored resources are not added to the history and
    # VCSs.  Also they are not returned in `Project.get_files()`.
    # Note that ``?`` and ``*`` match all characters but slashes.
    # '*.pyc': matches 'test.pyc' and 'pkg/test.pyc'
    # 'mod*.pyc': matches 'test/mod1.pyc' but not 'mod/1.pyc'
    # '.svn': matches 'pkg/.svn' and all of its children
    # 'build/*.o': matches 'build/lib.o' but not 'build/sub/lib.o'
    # 'build//*.o': matches 'build/lib.o' and 'build/sub/lib.o'
    prefs["ignored_resources"] = [
        "*.pyc",
        "*~",
        ".ropeproject",
        ".hg",
        ".svn",
        "_svn",
        ".git",
        ".tox",
    ]

    # Specifies which files should be considered python files.  It is
    # useful when you have scripts inside your project.  Only files
    # ending with ``.py`` are considered to be python files by
    # default.
    # prefs['python_files'] = ['*.py']

    # Custom source folders:  By default rope searches the project
    # for finding source folders (folders that should be searched
    # for finding modules).  You can add paths to that list.  Note
    # that rope guesses project source folders correctly most of the
    # time; use this if you have any problems.
    # The folders should be relative to project root and use '/' for
    # separating folders regardless of the platform rope is running on.
    # 'src/my_source_folder' for instance.
    # prefs.add('source_folders', 'src')

    # You can extend python path for looking up modules
    # prefs.add('python_path', '~/python/')

    # Should rope save object information or not.
    prefs["save_objectdb"] = True
    prefs["compress_objectdb"] = False

    # If `True`, rope analyzes each module when it is being saved.
    prefs["automatic_soa"] = True
    # The depth of calls to follow in static object analysis
    prefs["soa_followed_calls"] = 0

    # If `False` when running modules or unit tests "dynamic object
    # analysis" is turned off.  This makes them much faster.
    prefs["perform_doa"] = True

    # Rope can check the validity of its object DB when running.
    prefs["validate_objectdb"] = True

    # How many undos to hold?
    prefs["max_history_items"] = 32

    # Shows whether to save history across sessions.
    prefs["save_history"] = True
    prefs["compress_history"] = False

    # Set the number spaces used for indenting.  According to
    # :PEP:`8`, it is best to use 4 spaces.  Since most of rope's
    # unit-tests use 4 spaces it is more reliable, too.
    prefs["indent_size"] = 4

    # Builtin and c-extension modules that are allowed to be imported
    # and inspected by rope.
    prefs["extension_modules"] = []

    # Add all standard c-extensions to extension_modules list.
    prefs["import_dynload_stdmods"] = True

    # If `True` modules with syntax errors are considered to be empty.
    # The default value is `False`; When `False` syntax errors raise
    # `rope.base.exceptions.ModuleSyntaxError` exception.
    prefs["ignore_syntax_errors"] = False

    # If `True`, rope ignores unresolvable imports.  Otherwise, they
    # appear in the importing namespace.
    prefs["ignore_bad_imports"] = False

    # If `True`, rope will insert new module imports as
    # `from <package> import <module>` by default.
    prefs["prefer_module_from_imports"] = False

    # If `True`, rope will transform a comma list of imports into
    # multiple separate import statements when organizing
    # imports.
    prefs["split_imports"] = False

    # If `True`, rope will remove all top-level import statements and
    # reinsert them at the top of the module when making changes.
    prefs["pull_imports_to_top"] = True

    # If `True`, rope will sort imports alphabetically by module name instead
    # of alphabetically by import statement, with from imports after normal
    # imports.
    prefs["sort_imports_alphabetically"] = False

    # Location of implementation of
    # rope.base.oi.type_hinting.interfaces.ITypeHintingFactory In general
    # case, you don't have to change this value, unless you're an rope expert.
    # Change this value to inject you own implementations of interfaces
    # listed in module rope.base.oi.type_hinting.providers.interfaces
    # For example, you can add you own providers for Django Models, or disable
    # the search type-hinting in a class hierarchy, etc.
    prefs[
        "type_hinting_factory"
    ] = "rope.base.oi.type_hinting.factory.default_type_hinting_factory"


def project_opened(project):  # pylint: disable=unused-argument
    """This function is called after opening the project"""
    # Do whatever you like here!
