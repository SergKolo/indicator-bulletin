#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Serg Kolo <1047481448@qq.com>
# Date: February 12, 2017
# Purpose: Clipboard manager indicator for Ubuntu
# Tested on: Ubuntu 16.04 LTS
# Written for: http://askubuntu.com/q/842386/295286
#
# Licensed under The MIT License (MIT).
# See included LICENSE file or the notice below.
#
# Copyright © 2017 Sergiy Kolodyazhnyy
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import gi
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')
from gi.repository import AppIndicator3
from gi.repository import Notify
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from collections import OrderedDict
from base64 import b64encode, b64decode
from binascii import Error as ba_error
import datetime as dt
import subprocess
import threading
import tempfile
import signal
import json
import time
import sys
import os
import re


class IndicatorBulletin(object):

    def __init__(self):
        self.app = AppIndicator3.Indicator.new(
            'indicator-bulletin', "editpaste",
            AppIndicator3.IndicatorCategory.HARDWARE
        )

        # check if user wants to debug the indicator
        self.debug = False
        if len(sys.argv) == 2 and sys.argv[1] == 'debug':
            self.debug = True

        usrhome = os.environ['HOME']
        pjoin = os.path.join
        self.config_files = {
            'history_file': pjoin(usrhome, '.indicator-bulletin-history.json'),
            'config_file':  pjoin(usrhome, '.indicator-bulletin-config.json'),
            'pinned_file': pjoin(usrhome, '.indicator-bulletin-pinned.json')

        }

#        if os.path.exists(self.config_files['config_file']):
#            try:
#                self.read_history()
#            except Exception as e:
#                sys.stderr(">>> reading history:" + str(e) + "\n")
#                pass
        # Indicator UI settings defaults
        self.app_configs = self.read_config()
        # Set up GUI utilities
        self.clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.clip.connect('owner-change', self.write_history)
        self.notif = Notify.Notification.new("Notify")

        self.make_menu()
        thr = threading.Thread(target=self.check_history_file)
        thr.daemon = True
        thr.start()
        self.app.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    def check_history_file(self, *args):
        """ Checks history file for size, notifies if it's over
            1 Gibibyte in size """
        warning = self.config_files['history_file'] + ' is over 1 Gb in size'
        while True:
            if os.path.exists(self.config_files['history_file']) and os.stat(self.config_files['history_file']).st_size > 1024**3:
                self.info_dialog(warning)
            time.sleep(3600)

    def read_history(self, *args):
        """ reads history file contents """
        data = OrderedDict()
        try:
            # load existing data if exists
            with open(self.config_files['history_file']) as fd:
                data = json.load(fd)
                return OrderedDict(sorted(data.items(), reverse=True))
        except Exception as e:
            if (isinstance(e, FileNotFoundError) or
               isinstance(e, json.decoder.JSONDecodeError)):
                return None

    def write_history(self, *args):
        """ Writes text to history file"""
        copied_text = self.clip.wait_for_text()
        copied_uri = self.clip.wait_for_uris()
        data = OrderedDict()
        # If user copied files from file manager, ignore
        if copied_uri:
            return

        try:
            with open(self.config_files['history_file']) as fd:
                data = OrderedDict(json.load(fd))

        except Exception as e:
            if (isinstance(e, FileNotFoundError) or
                    isinstance(e, json.decoder.JSONDecodeError)):
                pass
            else:
                sys.stderr.write('>>> write_history:' + str(e) + '\n')

        # write current clipboard contents
        with open(self.config_files['history_file'], 'w') as fd:
            if self.debug:
                sys.stderr.write('>>> write_history: Appending to file' + '\n')
            timestamp = dt.datetime.now().strftime('%s')
            data[timestamp] = copied_text
            try:
                json.dump(data, fd, indent=4, sort_keys=True)
            except Exception as e:
                sys.stderr.write('>>> write_history:' + str(e) + '\n')
        self.make_menu()

    def write_to_clipboard(self, *args):
        """ Sets clipboard text """
        self.clip.set_text(args[-1], -1)

    def append_to_clipboard(self, *args):
        """ Combines existing cliboard contents
            with given text"""
        text = self.clip.wait_for_text()
        if not text:
            text = ""
        self.write_to_clipboard(self, text + " " + args[-1])

    def prepend_to_clipboard(self, *args):
        """ Inserts given text before cliboard contents"""
        text = self.clip.wait_for_text()
        if not text:
            text = ""
        self.write_to_clipboard(self, args[-1] + " " + text)

    def open_in_editor(self, *args):
        """ Creates temp file with clipboard contents
            for editing and inserts them back"""
        # TODO: figure out default editor detection
        temp = tempfile.mkstemp()[1]
        with open(temp, 'w') as fd:
            fd.write(args[-1])
        self.run_cmd(['xdg-open', temp])
        self.load_file(filename=temp)
        os.unlink(temp)
        if os.path.exists(temp + '~'):
            os.unlink(temp + '~')
        # TODO: because gedit creates the
        # filenames with ~ at the end for backup, the removal of
        # temp filename is not enough. But other editors such as vim
        # do the same. I cannot possibly implement removal of temp
        # files for all editors, so . . .what do I do here?

    def remove_from_history(self, *args):
        """ deletes entry from history file"""
        text = args[-1]
        data = self.read_history()
        if not data:
            return
        match = None
        for timestamp, record in data.items():
            if not record:
                continue
            if record == text:
                match = timestamp
        if match:
            data.pop(match)

        with open(self.config_files['history_file'], 'w') as fd:
            try:
                json.dump(data, fd, indent=4, sort_keys=True)
            except Exception as e:
                sys.stderr.write('>>> write_history:' + str(e) + '\n')
        self.make_menu()

    def display_date_range(self, *args):
        """ Extracts range of items based on timestamps
            from history files and displays it in zenity's
            textview dialog"""
        # no point in proceeding if history file is clear/empty/DNE
        data = self.read_history()
        print(data)
        if not data:
            return
        header = 'Enter time range\n'
        date_fmt = 'YYYY/MM/DD/HH:MM'
        header = header + 'Format:' + date_fmt
        header = header + '\n(24 clock)'
        cmd = ['zenity', '--text',
               header, '--forms',
               '--add-entry="Start date"',
               '--add-entry="End date"']
        dates = self.run_cmd(cmd)
        if not dates:
            return
        date_range = dates.decode().strip().split('|')
        if not len(date_range) == 2:
            self.error_dialog('Input error')
            return
        first = self.convert_to_seconds(date_range[0])
        last = self.convert_to_seconds(date_range[1])
        if last < first:
            info = 'End date should be older than start date.Try again'
            self.info_dialog(info)
            return self.display_date_range()

        if not first or not last:
            return
        temp = tempfile.mkstemp()[1]
        written = False
        try:
            with open(temp, 'w') as fd:
                for timestamp, entry in data.items():
                    ts = int(timestamp)
                    if ts > last:
                        continue
                    if ts < first:
                        break
                    entry_date = self.timestamp_to_date(timestamp)
                    if not entry:
                        continue
                    fd.write(entry_date + ': ' + entry + '\n')
                    written = True
            if written:
                cmd = ['zenity', '--text-info', '--filename', temp]
                self.run_cmd(cmd)
            else:
                self.info_dialog('Search done,nothing found')
        # except Exception as e:
            # self.error_dialog(str(e))
        finally:
            os.unlink(temp)

    def find_expression(self, *args):
        """ Searches stored text using python regex"""
        data = self.read_history()
        if not data:
            return
        cmd = ['zenity', '--entry', '--text', 'Enter expression to find:']
        expr = self.run_cmd(cmd)
        if not expr:
            return
        expr = expr.decode().strip()
        temp = tempfile.mkstemp()[1]
        if self.debug:
            sys.stderr.write('>>> find_expr,expr:' + expr + '\n')

        written = False
        with open(temp, 'w') as fd:
            for timestamp, text in sorted(data.items()):
                if not text:
                    continue
                if re.search(expr, text):
                    if self.debug:
                        sys.stderr.write(
                            '>>> find_expr:' + timestamp + ',' + text + '\n')
                    date = self.timestamp_to_date(timestamp)
                    fd.write(date + ':' + text + '\n')
                    written = True
        if written:
            subprocess.call(['zenity', '--text-info', '--filename', temp])
        else:
            subprocess.call(['zenity', '--info',
                             '--text', 'Search done. Nothing found'])
        if os.unlink(temp):
            if self.debug:
                sys.stderr('>>> find_expr: temp file unlinked' + '\n')

    def get_user_dir(self, **kwargs):
        for index, val in GLib.UserDirectory.__enum_values__.items():
            if val == kwargs['type']:
                return GLib.get_user_special_dir(index)

    def select_dir(self, *args):
        doc_dir = self.get_user_dir(
            type=GLib.UserDirectory.DIRECTORY_DOCUMENTS)
        cmd = ['zenity', '--file-selection',
               '--directory', '--filename', doc_dir]
        return self.run_cmd(cmd)

    def select_file(self, *args):
        doc_dir = self.get_user_dir(
            type=GLib.UserDirectory.DIRECTORY_DOCUMENTS)
        cmd = ['zenity', '--file-selection', '--filename', doc_dir]
        return self.run_cmd(cmd)

    def load_file(self, *args, **kwargs):
        if 'filename' not in kwargs.keys():
            filename = self.select_file()
            if not filename:
                return
        else:
            filename = kwargs['filename']

        if isinstance(filename, bytes):
            filename = filename.decode().strip()

        if not os.access(filename, os.R_OK):
            print(filename)
            self.error_dialog('No permission to read' + filename)
            return

        with open(filename) as fd:
            try:
                lines = fd.readlines()
                lines[-1] = lines[-1].strip()
            except Exception as e:
                self.error_dialog(str(e))
        if lines:
            return self.write_to_clipboard("".join(lines))

    def dump_to_file(self, *args):
        """ Outputs clipboard contents to a timestamped file"""
        destination = self.select_dir()
        if not destination:
            return
        destination = destination.decode().strip()
        if not os.access(destination, os.W_OK):
            self.error_dialog('No write permissions for ' + destination)
            return
        filename = 'clipboard_' + dt.datetime.now().strftime('%s') + '.txt'
        text = self.clip.wait_for_text()
        if not text:
            self.error_dialog('No text received')
            return
        with open(os.path.join(destination, filename), 'w') as fd:
            fd.write(text + '\n')
        notif_text = 'Clipboard contents written to ' + filename
        self.send_notif(self.notif, 'Indicator Bulletin', notif_text)

    # Editing
    def change_case(self, *args):
        """ Converts clipboard content to lower or upper case """
        text = self.clip.wait_for_text()
        if not text:
            self.error_dialog('Null text received')
        case = args[-1]
        if case == 'upper':
            self.write_to_clipboard(text.upper())
        if case == 'lower':
            self.write_to_clipboard(text.lower())

    def trim_dialog(self, *args):
        """ Dialog for choosing type and how many items to trim"""
        cmd = ['zenity', '--forms', '--text',
               'Trim ' + args[-1], '--add-combo', 'Method',
               '--combo-values', 'By words|By chars', '--add-entry',
               'How many(int)']
        user_input = self.run_cmd(cmd)
        if not user_input:
            return
        choices = user_input.decode().strip().split('|')
        if not choices[0]:
            self.error_dialog('Trim type not chosen')
            return
        if not choices[1].isdigit():
            self.error_dialog('Not a number:' + choices[1])
            return
        return tuple(choices)

    def trim_tail(self, *args):
        """ Strip elements from end"""
        text = self.clip.wait_for_text()
        if not text:
            self.info_dialog('Empty cliboard. Nothing to change')
            return
        new_text = str()

        pick = self.trim_dialog('tail')
        cutoff = -1 * int(pick[1])

        if pick[0] == 'By words':
            new_text = " ".join(text.split()[:cutoff])
        else:
            new_text = text[:cutoff]

        if not new_text:
            info = 'Empty text received (Too much removed?).'
            info = info + 'Clipboard unchanged'
            self.info_dialog(info)
            return
        self.write_to_clipboard(new_text)

    def trim_head(self, *args):
        """ Strip elements from beginning"""
        text = self.clip.wait_for_text()
        if not text:
            self.info_dialog('Empty cliboard. Nothing to change')
            return
        new_text = str()

        pick = self.trim_dialog('head')
        cutoff = int(pick[1])
        text = self.clip.wait_for_text()
        new_text = str()

        if pick[0] == 'By words':
            new_text = " ".join(text.split()[cutoff:])
        else:
            new_text = text[cutoff:]

        if not new_text:
            info = 'Empty text received (Too much removed?).'
            info = info + 'Clipboard unchanged'
            self.info_dialog(info)
            return
        self.write_to_clipboard(new_text)

    def replace_expr(self, *args):
        """ regex replacement """
        text = self.clip.wait_for_text()
        if not text:
            self.error_dialog('Empty clipboard - nothing to replace')
            return
        cmd = ['zenity', '--text',
               'Regex expression', '--forms',
               '--add-entry=PATTERN', '--add-entry=REPLACEMENT',
               '--separator', '\n']
        user_input = self.run_cmd(cmd)
        if not user_input:
            return
        regex = tuple(user_input.decode().strip().split('\n'))
        new_text = re.sub(regex[0], regex[1], text)
        self.write_to_clipboard(new_text)

    def base64_operation(self, *args):
        text = self.clip.wait_for_text()
        new_text = ""
        if not text:
            self.error_dialog('Empty clipboard - cannot convert')

        if args[-1] == 'encode':
            new_text = b64encode(text.encode())
        try:
            if args[-1] == 'decode':
                new_text = b64decode(text.encode())
        except ba_error:
            self.error_dialog("Incorrect padding in the given string")
            return
        if isinstance(new_text, bytes):
            new_text = new_text.decode()
        self.write_to_clipboard(new_text)
 
    def strip_whitespace(self,*args):
        text = self.clip.wait_for_text()
        if not text:
           return
        if args[-1] == 0:
            self.write_to_clipboard(text.lstrip())
        if args[-1] == 1:
            self.write_to_clipboard(text.rstrip())
# ---

    def clear_all(self, *args):
        """ Deletes all previously stored text items"""
        with open(self.config_files['history_file'], 'w') as fd:
            fd.write("")
        self.make_menu()

    def touch_file(self, filepath):
        with open(filepath, "w") as f:
            f.write("")

    # configuration handling
    def read_config(self):
        """ reads user config data """
        defaults = {'menu_length': 10,
                    'text_width': 30
                    }
        try:
            with open(self.config_files['config_file']) as f:
                data = json.load(f)
                return data
        except FileNotFoundError:
            self.touch_file(self.config_files['config_file'])
            self.write_config(defaults)
        except json.decoder.JSONDecodeError:
            return defaults

    def write_config(self, config_map):
        """ Writes user configuration to file"""
        with open(self.config_files['config_file'], 'w') as f:
            json.dump(config_map, f, indent=4)

    def read_pinned(self,*args):
        try:
            with open(self.config_files['pinned_file']) as f:
                data = json.load(f)
                return data
        except FileNotFoundError:
            self.touch_file(self.config_files['pinned_file'])
        except json.decoder.JSONDecodeError:
            return 

    def write_pinned(self,*args):
        data = self.read_pinned()
        if not os.path.exists(self.config_files['pinned_file']):
            return
        if not data: 
            data = {"pinned": [args[-1]]}
        else:
            data["pinned"].append(args[-1])

        # handle exceptions
        with open(self.config_files['pinned_file'],'w') as fd:
            json.dump(data,fd,indent=4)
        return self.make_menu()

    def remove_pinned(self,*args):
        data =  self.read_pinned()
        for x,i in enumerate(data["pinned"]):
            if i == args[-1]:
                print(x,i)
                data["pinned"].pop(x)
                break
        #handle exceptions, remember to call make_menu() outside 
        with open(self.config_files['pinned_file'],'w') as fd:
            json.dump(data,fd,indent=4)
        return self.make_menu()
             
       
    def error_dialog(self, *args):
        subprocess.call(['zenity', '--error', '--text', args[-1]])

    def info_dialog(self, *args):
        subprocess.call(['zenity', '--info', '--text', args[-1]])

    def add_submenu(self, top_menu, label, **kwargs):
        """ utility function for adding submenus"""
        menuitem = Gtk.MenuItem(label)
        if kwargs and 'icon' in kwargs.keys():
            menuitem = Gtk.ImageMenuItem.new_with_label(label)
            menuitem.set_always_show_image(True)
            if '/' in kwargs['icon']:
                icon = Gtk.Image.new_from_file(kwargs['icon'])
            else:
                icon = Gtk.Image.new_from_icon_name(kwargs['icon'], 48)
            menuitem.set_image(icon)
        submenu = Gtk.Menu()
        menuitem.set_submenu(submenu)
        top_menu.append(menuitem)
        menuitem.show()
        return submenu

    # TODO: rewrite this with kwargs
    def add_menu_item(self, menu_obj, item_type, image, label, action, args):
        """ dynamic function that can add menu items depending on
            the item type and other arguments"""
        menu_item, icon = None, None
        if item_type is Gtk.ImageMenuItem and label:
            menu_item = Gtk.ImageMenuItem.new_with_label(label)
            menu_item.set_always_show_image(True)
            if '/' in image:
                icon = Gtk.Image.new_from_file(image)
            else:
                icon = Gtk.Image.new_from_icon_name(image, 48)
            menu_item.set_image(icon)
        elif item_type is Gtk.ImageMenuItem and not label:
            menu_item = Gtk.ImageMenuItem()
            menu_item.set_always_show_image(True)
            if '/' in image:
                icon = Gtk.Image.new_from_file(image)
            else:
                icon = Gtk.Image.new_from_icon_name(image, 16)
            menu_item.set_image(icon)
        elif item_type is Gtk.MenuItem:
            menu_item = Gtk.MenuItem(label)
        elif item_type is Gtk.SeparatorMenuItem:
            menu_item = Gtk.SeparatorMenuItem()
        if action:
            menu_item.connect('activate', action, *args)
        menu_obj.append(menu_item)
        menu_item.show()
        return menu_item

    def add_entry_submenus(self,entry_menu,text,**kwargs):

        item = [entry_menu, Gtk.ImageMenuItem, 'insert-text',
                'Insert', self.write_to_clipboard, [text]]
        self.add_menu_item(*item)

        item = [entry_menu, Gtk.ImageMenuItem, 'gtk-add',
                'Append', self.append_to_clipboard, [text]]
        self.add_menu_item(*item)

        item = [entry_menu, Gtk.ImageMenuItem, 'gtk-add',
                'Prepend', self.prepend_to_clipboard, [text]]
        self.add_menu_item(*item)

        item = [entry_menu, Gtk.ImageMenuItem, 'text-editor',
                'Open in editor', self.open_in_editor, [text]]
        self.add_menu_item(*item)

        if kwargs['history']:
            item = [entry_menu, Gtk.ImageMenuItem, 'edit-clear',
                    'Remove', self.remove_from_history, [text]]
            self.add_menu_item(*item)

            item = [entry_menu,Gtk.ImageMenuItem,'starred',
                    'Add to pinned', self.write_pinned,[text]]
            self.add_menu_item(*item)
                    

    def make_menu(self, *args):
        """ generates entries in the indicator"""
        if hasattr(self, 'app_menu'):
            for item in self.app_menu.get_children():
                self.app_menu.remove(item)
        self.app_menu = Gtk.Menu()

        item = [self.app_menu, Gtk.MenuItem,
                None, 'RECENT TEXT',
                None, [None]]
        header = self.add_menu_item(*item)
        header.set_sensitive(False)

        history = self.read_history()
        if history:
            counter = 0
            for timestamp, text in history.items():
                if not text:
                    continue
                if counter > self.app_configs['menu_length']:
                    break
                label = text
                if len(text) > self.app_configs['text_width']:
                    label = text[:self.app_configs['text_width']] + '...'
                text_entry = self.add_submenu(self.app_menu, label)
                self.add_entry_submenus(text_entry,text,history=True)
                counter += 1
        else:

            item = [self.app_menu, Gtk.MenuItem,
                    None, 'None',
                    None, [None]]
            self.add_menu_item(*item)

                    
        item = [self.app_menu, Gtk.MenuItem,
                None, 'OTHER OPTIONS',
                None, [None]]
        header = self.add_menu_item(*item)
        header.set_sensitive(False)
        # Pinned entries
        pinned_menu = self.add_submenu(self.app_menu,"Pinned",icon='starred')
        pinned_items = self.read_pinned()
        if pinned_items:
            for text in pinned_items["pinned"]:
                label = text
                if len(text) > self.app_configs['text_width']:
                    label = text[:self.app_configs['text_width']] + '...'
                text_entry = self.add_submenu(pinned_menu, label)
                self.add_entry_submenus(text_entry,text,history=False)
                item = [text_entry,Gtk.ImageMenuItem,
                        'gtk-remove','Remove',
                        self.remove_pinned,[text]
                ]
                self.add_menu_item(*item)
        # Search options
        search_menu = self.add_submenu(
            self.app_menu, 'Find text', icon='gtk-find')
        item = [search_menu, Gtk.MenuItem,
                None, 'Find by expression',
                self.find_expression, [None]]
        self.add_menu_item(*item)

        item = [search_menu, Gtk.MenuItem,
                None, 'Show date range',
                self.display_date_range, [None]]
        self.add_menu_item(*item)

        # ---

        load_menu = self.add_submenu(
            self.app_menu, 'File operations', icon='gtk-open')
        item = [load_menu, Gtk.MenuItem,
                None, 'From file',
                self.load_file, [None]]
        self.add_menu_item(*item)

        item = [load_menu, Gtk.MenuItem,
                None, 'Dump to file',
                self.dump_to_file, [None]]
        self.add_menu_item(*item)
        # ---
        edit_menu = self.add_submenu(self.app_menu, 'Edit', icon='text-editor')
        item = [edit_menu, Gtk.MenuItem,
                None, 'To uppercase',
                self.change_case, ['upper']]
        self.add_menu_item(*item)

        item = [edit_menu, Gtk.MenuItem,
                None, 'To lowercase',
                self.change_case, ['lower']]
        self.add_menu_item(*item)

        item = [edit_menu, Gtk.MenuItem,
                None, 'Trim from end',
                self.trim_tail, [None]]
        self.add_menu_item(*item)

        item = [edit_menu, Gtk.MenuItem,
                None, 'Trim from beginning',
                self.trim_head, [None]]
        self.add_menu_item(*item)

        item = [edit_menu, Gtk.MenuItem,
                None, 'Replace expression',
                self.replace_expr, [None]]
        self.add_menu_item(*item)

        item = [edit_menu, Gtk.MenuItem,
                None, 'Base64 encode',
                self.base64_operation, ['encode']]
        self.add_menu_item(*item)

        item = [edit_menu, Gtk.MenuItem,
                None, 'Base64 decode',
                self.base64_operation, ['decode']]
        self.add_menu_item(*item)

        item = [edit_menu, Gtk.MenuItem,
                None, 'Strip leading whitespace/newline',
                self.strip_whitespace, [0]]
        self.add_menu_item(*item)

        item = [edit_menu, Gtk.MenuItem,
                None, 'Strip trailing whitespace/newline',
                self.strip_whitespace, [1]]
        self.add_menu_item(*item)
        # ---

        item = [self.app_menu, Gtk.ImageMenuItem,
                'user-trash', 'Clear all',
                self.clear_all, [None]]
        self.add_menu_item(*item)
        item = [self.app_menu, Gtk.ImageMenuItem,
                'exit', 'Quit',
                self.quit, [None]]
        self.add_menu_item(*item)

        self.app.set_menu(self.app_menu)

    def send_notif(self, n, title, text):
        """sends bubble notification"""
        try:
            if Notify.init(__file__):
                n.update(title, text)
                n.set_urgency(2)
                if not n.show():
                    raise SyntaxError("sending notification failed!")
            else:
                raise SyntaxError("can't initialize notification!")
        except SyntaxError as error:
            if self.debug:
                print(">> DEBUG:", str(error))
            if error == "sending notification failed!":
                Notify.uninit()
        else:
            Notify.uninit()

    def run(self):
        """ Launches the indicator """
        Gtk.main()

    def quit(self, *args):
        """ closes indicator """
        Gtk.main_quit()

    # Date and time functions
    def timestamp_to_date(self, *args):
        timestamp = int(args[-1])
        dtobj = dt.datetime.fromtimestamp(timestamp)
        return dtobj.strftime('%Y %b %d %H:%M:%S')

    def convert_to_seconds(self, *args):
        date_fmt = '%Y/%m/%d/%H:%M'
        try:
            dtobj = dt.datetime.strptime(args[-1], date_fmt)
        except ValueError:
            self.error_dialog('Improper date format:' + args[-1])
            return
        return int(dtobj.strftime('%s'))

    def run_cmd(self, cmdlist):
        """ Reusable function for running external commands """
        try:
            stdout = subprocess.check_output(cmdlist)
        except subprocess.CalledProcessError as sperror:
            if self.debug:
                print(">>> DEBUG: subprocess error\n", repr(sperror))
        else:
            if stdout:
                return stdout


def main():
    """ defines program entry point """
    indicator = IndicatorBulletin()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    indicator.run()

if __name__ == '__main__':
    main()
