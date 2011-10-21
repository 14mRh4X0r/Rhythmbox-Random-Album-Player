'''
Plugin for Rythmbox that random plays songs sorted by album, track-number randomly
Copyright (C) 2011  Javon Harper <javharper@gmail.com>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''
import random

import rb
from gi.repository import RB
from gi.repository import GObject, Gtk, Peas

ui_definition = """
<ui>
  <menubar name="MenuBar">
    <menu name="ControlMenu" action="Control">
      <menuitem name="Random Album" action="RandomAlbum"/>
    </menu>
  </menubar>
  <toolbar name="ToolBar">
    <toolitem name="Random Album" action="RandomAlbum"/>
  </toolbar>
</ui>
"""

class RandomAlbumPlugin (GObject.Object, Peas.Activatable): 
  __gtype_name__ = 'RandomAlbumPlugin'

  object = GObject.property (type = GObject.Object)

  def __init__(self):
    GObject.Object.__init__(self)
  
  def queue_random_album(self):
    shell = self.object
    #find all of the albums in the user's library
    albums = []
    library = shell.props.library_source
    for row in library.props.query_model:
      entry = row[0]
      album_name = entry.get_string(RB.RhythmDBPropType.ALBUM)
      if (album_name not in albums):
        albums.append(album_name)
    
    #choose a random album
    selected_album = albums[random.randint(0, len(albums) - 1)]
    print 'queuing ' + selected_album
    
    #find all the songs from that album
    song_info = []
    for row in library.props.query_model:
      entry = row[0]
      album = entry.get_string(RB.RhythmDBPropType.ALBUM)
      if album == selected_album:
        track_num = entry.get_ulong(RB.RhythmDBPropType.TRACK_NUMBER)
        song_info.append((entry, track_num))

    #sort the songs
    song_info = sorted(song_info, key=lambda song_info: song_info[1])

    #add the songs to the play queue
    for info in song_info:
      shell.props.queue_source.add_entry(info[0], -1)

  #loads the plugin  
  def do_activate(self):
    #displays the icon on the toolbar
    icon_file_name = '/usr/share/icons/gnome/22x22/apps/zen-icon.png'
    iconsource = Gtk.IconSource();
    iconsource.set_filename(icon_file_name)
    iconset = Gtk.IconSet()
    iconset.add_source(iconsource)
    iconfactory = Gtk.IconFactory()
    iconfactory.add('random-album-button', iconset)
    iconfactory.add_default();

    self.__action = Gtk.Action(name='RandomAlbum', label=_('Random Album...'),
                              tooltip=_('Plays a random album...'),
                              stock_id='random-album-button')
    shell = self.object
    self.__action.connect('activate', self.random_album, shell)

    self.__action_group = Gtk.ActionGroup(name='RandomAlbumActionGroup')
    self.__action_group.add_action(self.__action)
    uim = shell.props.ui_manager
    uim.insert_action_group(self.__action_group, -1)
    uim.add_ui_from_string(ui_definition)

  #removed the ui modifications and unloads the plugin 
  def do_deactivate(self):
    shell = self.object
    uim = shell.props.ui_manager
    uim.remove_action_group(self.__action_group)
    uim.remove_ui(self.__ui_id)
    uim.ensure_update()
    del self.__action_group
    del self.__action

  def random_album(self, event, shell):
    #get URIs of all the songs in the queue and remove them
    print 'Removing songs from play queue'
    play_queue = shell.props.queue_source
    for row in play_queue.props.query_model:
      entry = row[0]
      shell.props.queue_source.remove_entry(entry)

    #queue a random album
    self.queue_random_album()

    #start the music!(well, first stop it, but it'll start up again.)
    print 'Playing Album'
    player = shell.props.shell_player
    player.stop()
    player.set_playing_source(shell.props.queue_source)
    # The boolean is actually unused
    # (see shell/rb-shell-player.c:rb_shell_player_playpause())
    player.playpause(True)

    #scroll to song playing
    shell.props.shell_player.play()
    library = shell.props.library_source
    content_viewer = library.get_entry_view()
    #content_viewer.scroll_to_entry(player.get_playing_entry())