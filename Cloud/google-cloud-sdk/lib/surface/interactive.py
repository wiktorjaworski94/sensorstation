# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Extensible interactive shell with auto completion and help."""

from __future__ import unicode_literals

import StringIO

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.shell import application
from googlecloudsdk.command_lib.shell import bindings
from googlecloudsdk.command_lib.shell import config as configuration
from googlecloudsdk.core import properties
from googlecloudsdk.core.document_renderers import render_document


_FEATURES = """
* auto-completion for *gcloud* commands, flags and resource arguments
* support for other CLIs including *bq*, *gsutil* and *kubectl*
* state preserved across commands: *cd*, local and environment variables
"""

_SPLASH = """
# Welcome to the gcloud interactive shell environment.

Features in this release include:
""" + _FEATURES + """
Run *$ gcloud feedback* to report bugs or request new features.

"""


def _GetKeyBindingsHelp():
  """Returns the function key bindings help markdown."""
  lines = []
  for key in bindings.KeyBindings().bindings:
    if key.help_text:
      lines.append('\n{}:::'.format(key.GetLabel(markdown=True)))
      lines.append(key.help_text)
  return '\n'.join(lines)


def _GetPropertiesHelp():
  """Returns the properties help markdown."""
  lines = []
  for prop in sorted(properties.VALUES.interactive, key=lambda p: p.name):
    if prop.help_text:
      lines.append('\n*{}*:::'.format(prop.name))
      lines.append(prop.help_text)
      default = prop.default
      if default is not None:
        if isinstance(default, basestring):
          default = '"{}"'.format(default)
        else:
          if default in (False, True):
            default = str(default).lower()
          default = '*{}*'.format(default)
        lines.append('The default value is {}.'.format(default))
  return '\n'.join(lines)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Interactive(base.Command):
  """Start the gcloud interactive shell.

  *{command}* provides an enhanced *bash*(1) command line with features that
  include:
  {features}

  ### Display

  The *{command}* display window is divided into 5 sections, described here
  from top to bottom.

  *Previous Output*::

  Command output scrolls above the command input section as commands are
  executed.

  *Command Input*::

  Commands are typed, completed and edited in this section. The default prompt
  is "$ ". If a context has been set then its tokens are prepopulated before
  the cursor.

  *Active Help*::

  Help text snippets for _known_ commands are displayed in this section as
  commands are typed.

  *Status Display*::

  Contains the current *gcloud* project and user.

  *Function Keys*::

  Function keys toggle mode/state settings or run specific actions.
  {bindings}

  ### Auto and TAB Completion

  Command completions are displayed in a scrolling pop-up window. Use TAB and
  up/down keys to navigate the completions, and ENTER/RETURN to select the
  highlighted completion. Completions for _known_ commands, flags and static
  flag values are displayed automatically. Positional and dynamic flag value
  completions for _known_ commands are displayed after TAB is entered. TAB
  completion for unknown commands defers to *bash*(1), but using the
  *interactive* user interface. Absent specific command information, a
  file/path completer is used when TAB is entered for unknown positionals
  (arguments that do not start with '-').

  ### Control Characters

  Control characters affect the currently running command or the current
  command line being entered at the prompt.

  *^C*:::
  If a command is currently running then that command is interrupted, usually
  causing the command to terminate. Otherwise ^C clears the current command
  line.

  *^D*:::
  Exits when entered as the first character at the command prompt. You can
  also run the *exit* command at the prompt.

  *^W*:::
  If a command is not currently running then the last word on the command line
  is deleted. This is handy for "walking back" partial completions.

  ### Command history

  *{command}* maintains persistent command history across sessions.

  #### emacs mode

  *^N*::: Move ahead one line in the history.
  *^P*::: Move back one line in the history.
  *^R*::: Search backwards in the history.

  #### vi mode

  /::: Search backwards in the history.
  *j*::: Move ahead one line in the history.
  *k*::: Move back one line in the history.
  *n*::: Search backwards for the next match.
  *N*::: Search forwards for the next match.

  #### history search mode

  *ENTER/RETURN*::: Retrieve the matched command line from the history.
  *^R*::: Search backwards for the next match.
  *^S*::: Search forwards for the next match.

  ### Layout Configuration

  Parts of the layout are configurable via
  *$ gcloud config set* interactive/_property_. These properties are only
  checked at startup. You must exit and restart to see the effects of new
  settings.
  {properties}

  ## NOTES

  Although the goal is to provide the same experience across all platforms,
  the underlying open-source libraries are biased in this decreasing order:
  *linux*, *macos*, *Windows*. As the alpha implementation matures the platform
  differences will subside.

  For a *bash*(1) experience on *Windows* install *git*(1) and the *git*
  (MinGW) *bash* will be used.

  Please run *$ gcloud feedback* to report bugs or request new features.
  """

  detailed_help = {
      'bindings': _GetKeyBindingsHelp,
      'features': _FEATURES,
      'properties': _GetPropertiesHelp,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--context',
        help=('The default command context. This is a string containing a '
              'command name, flags and arguments. The context is prepopulated '
              'in each command line. You can inline edit any part of the '
              'context, or ^C to eliminate it.'))
    parser.add_argument(
        '--hidden',
        hidden=True,
        action='store_true',
        default=None,
        help='Enable completion of hidden commands and flags.')
    parser.add_argument(
        '--prompt',
        help='The interactive shell prompt.')
    parser.add_argument(
        '--suggest',
        hidden=True,
        action='store_true',
        default=None,
        help=('Enable auto suggestion from history. The defaults are currently '
              'too rudimentary for prime time.'))

  def Run(self, args):
    if not args.quiet:
      render_document.RenderDocument(fin=StringIO.StringIO(_SPLASH))
    config = configuration.Config(
        context=args.context,
        hidden=args.hidden,
        prompt=args.prompt,
        suggest=args.suggest,
    )
    application.main(cli=self._cli_power_users_only, args=args, config=config)
