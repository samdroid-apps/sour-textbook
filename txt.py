from gi.repository import Gtk
import json
import os
import logging
import tarfile

from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarButton	
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton

class ActivityRenderer(Gtk.Box):

	def __init__(self, data, progress, path):
		Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
		
		label = Gtk.Label()
		label.set_markup(data['info'])
		self.pack_start(label, True, False, 0)
		label.show()
		
		activity_box = Gtk.Box()
		self.pack_start(activity_box, True, False, 0)
		activity_box.show()
		
		activity_name = Gtk.Label()
		activity_name.set_markup('<b>{}</b>'.format(data['type']))
		activity_box.pack_start(activity_name, True, False, 0)
		activity_name.show()
	
	def get_progress(self):
		return None

class ImageRednerer(Gtk.Image):

	def __init__(self, data, progress, path):
		Gtk.Image.__init__(self)
		
		filename = data.get('filename', '')
		self.set_from_file(os.path.join(path, filename))
	
	def get_progress(self):
		return None

class TextRenderer(Gtk.Label):
	
	def __init__(self, data, progress, path):
		Gtk.Label.__init__(self)
		self.set_markup(data)
		self.set_line_wrap(True)
		self.set_justify(Gtk.Justification.FILL)
	
	def get_progress(self):
		return None
		
class FreeResponceQuizView(Gtk.Box):

	def __init__(self, data, progress, path):
		Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL,
		                 spacing=0)
		self._data = data
		self._question = progress if progress else 0
		
		self._label = Gtk.Label()
		self.pack_start(self._label, True, False, 64)
		self._label.show()
		
		self._wrong_label = Gtk.Label("Wrong, the answer was:")
		self.pack_start(self._wrong_label, True, False, 0)
		
		self._answer_box = Gtk.Box()
		self.pack_end(self._answer_box, True, False, 0)
		self._answer_box.show()
		
		self._entry = Gtk.Entry()
		self._entry.connect('activate', self._next_question)
		self._answer_box.pack_start(self._entry, True, True, 0)
		self._entry.show()
		
		self._skip = Gtk.Button(label="Skip")
		self._skip.connect('clicked', self._skip_question)
		self._answer_box.pack_start(self._skip, True, False, 0)
		
		self._redo = Gtk.Button(label="Redo the Quiz")
		self._redo.connect('clicked', self._redo_quiz)
		self._answer_box.pack_start(self._redo, True, False, 0)
		
		self._setup_question()
		
	def _next_question(self, widget):
		user_answer = str(self._entry.get_text()).strip().lower()
		answer = str(self._data[self._question].get('answer', '')). \
							strip().lower()
		if user_answer == answer:
			self._question += 1
			if self._question == len(self._data):
				self._victory()
			else:
				self._setup_question()
		else:
			self._wrong_label.show()
			self._entry.set_text(answer)
			self._entry.set_editable(False)
			self._skip.show()
			
	def _victory(self):
		self._label.set_markup("<b>Done</b>")
		self._entry.set_text('')
		self._entry.set_placeholder_text("You've Finished :)")
		self._entry.set_editable(False)
		self._redo.show()
			
	def _skip_question(self, widget):
		self._entry.set_editable(True)
		self._wrong_label.hide()
		self._skip.hide()
		self._question += 1
		if self._question == len(self._data):
			self._victory()
		else:
			self._setup_question()
			
	def _redo_quiz(self, widget):
		self._redo.hide()
		self._entry.set_editable(True)
		self._question = 0
		self._setup_question()
			
	def _setup_question(self):
		if self._question == 0:
			self._entry.set_placeholder_text('Start the quiz!')
		else:
			self._entry.set_placeholder_text('What\'s the answer?')
		self._entry.set_text('')
		text = self._data[self._question].get('text', 'ERROR')
		self._label.set_markup('<b>{}</b>'.format(text))
		
	def get_progress(self):
		return self._question
		
TYPES = {'text' : TextRenderer, 'free-responce-quiz' : FreeResponceQuizView,
		 None : TextRenderer, 'image' : ImageRednerer, 
		 'activity' : ActivityRenderer}


class TextBookView(Gtk.ScrolledWindow):

	def __init__(self, textbook, activity):
		Gtk.ScrolledWindow.__init__(self)
		self._kids = []
		self._activity = activity
		
		self._main_view = Gtk.Box.new(Gtk.Orientation.VERTICAL, 16)
		self.add(self._main_view)
		self._main_view.show()
		self._setup_controls()
		
		self._textbook = textbook
		self._pos = self._textbook.get('pos', 0)
		page_data = json.load(open(os.path.join(self._activity.path,
				self._textbook['pages'][self._pos]['file'])))
		self._setup_with_data(page_data)
			
	def _setup_controls(self):
		self._title = Gtk.Label()
		self._main_view.pack_start(self._title, True, False, 0)
		self._title.show()
	
		control_box = Gtk.Box()
		self._main_view.pack_end(control_box, True, False, 0)
		control_box.show()
		
		control_next = Gtk.Button.new_from_stock('gtk-go-forward')
		control_next.set_always_show_image(True)
		control_next.set_image_position(Gtk.PositionType.RIGHT)
		control_next.connect("clicked", self.next_page)
		control_next.show()
		control_box.pack_end(control_next, True, False, 0)
		self._main_view.pack_end(control_box, True, False, 0)
		
		control_prev = Gtk.Button.new_from_stock('gtk-go-back')
		control_prev.set_always_show_image(True)
		control_prev.set_image_position(Gtk.PositionType.LEFT)
		control_prev.connect("clicked", self.prev_page)
		control_prev.show()
		control_box.pack_start(control_prev, True, False, 0)
			
	def _setup_with_data(self, data):
		for i in self._kids:
			self._main_view.remove(i)
			del i
			
		self._data = data
		logging.error(data)
		
		for item in data.get('content', []):
			renderer_type = TYPES[item.get('type', None)]
			item_data = item.get('data', None)
			item_progress = item.get('progress', None)
			renderer = renderer_type(item_data, item_progress,
							self._activity.path)
			self._main_view.pack_start(renderer, True, False, 0)
			renderer.show()
			self._kids.append(renderer)
			
		title_text = data.get('title', '')
		self._title.set_markup('<span font="Serif 18" variant="smallcaps">{}</span>'.format(title_text))
			
		self.save_state()
			
	def next_page(self, widget):
		self._save_page()
		self._pos += 1
		if self._pos >= len(self._textbook['pages']):
			self._pos = 0
		page_data = json.load(open(os.path.join(self._activity.path,
				self._textbook['pages'][self._pos]['file'])))
		self._setup_with_data(page_data)
		
	def prev_page(self, widget):
		self._save_page()
		self._pos -= 1
		if self._pos == -1:
			self._pos = len(self._textbook['pages']) - 1
		page_data = json.load(open(os.path.join(self._activity.path,
				self._textbook['pages'][self._pos]['file'])))
		self._setup_with_data(page_data)
		
	def set_page(self, index):
		self._save_page()
		self._pos = index
		page_data = json.load(open(os.path.join(self._activity.path,
				self._textbook['pages'][self._pos]['file'])))
		self._setup_with_data(page_data)
		
	def _save_page(self):
		page_data = json.load(open(os.path.join(self._activity.path,
				self._textbook['pages'][self._pos]['file'])))
		new_content = []
		for i in zip(page_data['content'], self._kids):
			i[0]['progress'] = i[1].get_progress()
			new_content.append(i[0])
		page_data['content'] = new_content
		out_file = open(os.path.join(self._activity.path,
				self._textbook['pages'][self._pos]['file']),
				'w')
		json.dump(page_data, out_file)
		
	def save_state(self):
		self._textbook['pos'] = self._pos
		json.dump(self._textbook,
			open(os.path.join(self._activity.path,'textbook.json'),
						'w'))
		
class ContentsView(Gtk.TreeView):
	
	def __init__(self, textbook, textbook_view):
		self._textbook_view = textbook_view
		self._textbook = textbook
		self._id_to_index = {}
		self._setup_id_to_index()
		
		self._data_store = Gtk.TreeStore(str, int)
		self._path_to_file = {}
		
		self._setup_ds()
		Gtk.TreeView.__init__(self, self._data_store)
		
		renderer = Gtk.CellRendererText()
		column = Gtk.TreeViewColumn("Contents", renderer, text=0)
		self.append_column(column)
		
		select = self.get_selection()
		select.connect("changed", self.on_tree_selection_changed)
		
	def _setup_id_to_index(self):
		for item in enumerate(self._textbook['pages']):
			self._id_to_index[item[1]['id']] = item[0]
		
	def _add_recursive(self, contents, parent):
		for i in contents:
			item = self._data_store.append(parent, (i['title'],
								i['id']))
			self._add_recursive(i.get('children', []), item)
		
	def _setup_ds(self):
		for i in self._textbook['contents']:
			item = self._data_store.append(None, (i['title'],
								i['id']))
			self._add_recursive(i.get('children', []), item)
			
	def on_tree_selection_changed(self, selection):
		model, treeiter = selection.get_selected()
		if treeiter != None:
			id_ = model[treeiter][1]
			index = self._id_to_index[id_]
			self._textbook_view.set_page(index)
		
	
class TextBookActivity(activity.Activity):
	
	def __init__(self, handle):	
		super(TextBookActivity, self).__init__(handle)
		
		self._paned = Gtk.Paned()
		self.set_canvas(self._paned)
		self._paned.show()
		self._is_toolbar_setup = False
		
		self._load_textbook(None)
		
		self.connect("visibility-notify-event", self._visibility_changed)
		
	def read_file(self, filename):
		self._load_textbook(filename)
		
	def _load_textbook(self, path):
		self.path = os.path.join(self.get_activity_root(), "instance")
		
		if not os.path.isfile(os.path.join(self.path, 'textbook.json')):
			if path:
				tar = tarfile.open(path)
				tar.extractall(self.path)
			else:
				return
		
		self._textbook = json.load(open(os.path.join(self.path,
							 'textbook.json')))
							 
		self._textbook_view = TextBookView(self._textbook, self)
		self._paned.pack2(self._textbook_view)
		self._textbook_view.show()
		
		self._contents = ContentsView(self._textbook, self._textbook_view)
		self._paned.pack1(self._contents)
		self._contents.show()
		
		if not self._is_toolbar_setup:
			self._setup_toolbar()
							 
	def _visibility_changed(self, widget, event):
		self._textbook_view.save_state()
		
	def _setup_toolbar(self):
		self._toolbar_box = ToolbarBox()
		activity_button = ActivityToolbarButton(self)
		self._toolbar_box.toolbar.insert(activity_button, 0)
		self.set_toolbar_box(self._toolbar_box)
		self._toolbar = self.get_toolbar_box().toolbar
		
		control_prev = Gtk.ToolButton.new_from_stock('gtk-go-back')
		control_prev.connect("clicked", self._textbook_view.prev_page)
		self._toolbar.insert(control_prev, -1)
		
		control_next = _prev = Gtk.ToolButton.new_from_stock('gtk-go-forward')
		control_next.connect("clicked", self._textbook_view.next_page)
		self._toolbar.insert(control_next, -1)
		
		separator = Gtk.SeparatorToolItem()
		separator.props.draw = False
		separator.set_expand(True)
		self._toolbar.insert(separator, -1)
		self._toolbar.insert(StopButton(self), -1)
		self.get_toolbar_box().show_all()
		
		self._is_toolbar_setup = True
