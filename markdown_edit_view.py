import logging
import os
import shutil

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GtkSource
from gi.repository.GdkPixbuf import Pixbuf

from sugar3.graphics.objectchooser import ObjectChooser
from sugar3.graphics.objectchooser import FILTER_TYPE_GENERIC_MIME

INTO_DEFS_CONSTANT = "<!--- ~-~-~QWERTY: D3FS N0W!: WSAD~-~-~ -->"
UID = 0

class markdownEditView(Gtk.Paned):
	def __init__(self, markdown, activity):
		Gtk.Paned.__init__(self)
		self._activity = activity		

		self._sourcebuffer = GtkSource.Buffer()
		self._sourcebuffer.set_highlight_syntax(True)
		self._sourcebuffer.set_text(markdown)

		self._sourceview = GtkSource.View(buffer=self._sourcebuffer)
		self.add2(self._sourceview)
		self._sourceview.show()

		self._setup_list()

	def _setup_list(self):
		b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

		self._iconstore = Gtk.ListStore(Pixbuf, str, str)
		self._iconview = Gtk.IconView.new_with_model(self._iconstore)
		self._iconview.enable_model_drag_source(
				Gdk.ModifierType.BUTTON1_MASK,
				[], Gdk.DragAction.COPY)

		self._iconview.drag_source_add_text_targets()
		self._iconview.connect("drag-data-get", self.on_drag_data_get)
		b.pack_start(self._iconview, True, True, 0)
		self._iconview.show()

		pr = Gtk.CellRendererPixbuf()
		pr.set_alignment(0.5, 0.5)
		self._iconview.pack_start(pr, True)
		self._iconview.set_cell_data_func(pr, self._img_data_func,
									None)

		tr = Gtk.CellRendererText()
		tr.set_alignment(0.5, 0.5)
		tr.set_property("editable", True)
		tr.connect("edited", self._title_text_edited)
		self._iconview.pack_start(tr, True)
		self._iconview.set_cell_data_func(tr, self._title_data_func,
									None)

		self._add_bnt = Gtk.Button(label="+")
		self._add_bnt.connect("clicked", self._add_new)
		b.pack_start(self._add_bnt, False, False, 0)
		self._add_bnt.show()

		self.add1(b)
		b.show()

	def _title_text_edited(self, widget, path, text):
		self._iconstore[path][1] = text

	def _add_new(self, caller):
		global UID
		chooser = ObjectChooser(self._activity, what_filter='Image',	
					filter_type=FILTER_TYPE_GENERIC_MIME,
					show_preview=True)
		result = chooser.run()
		if result == Gtk.ResponseType.ACCEPT:
			file_path = chooser.get_selected_object().file_path
			shutil.copy(file_path, self._activity.path)
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
							file_path,
							200, -1, True)
			self._iconstore.append([pixbuf, str(UID),
						os.path.basename(file_path)])
			UID += 1

	def _title_data_func(self, view, cell, store, i, data):
		title = store.get_value(i, 1)
		cell.props.markup = title

	def _img_data_func(self, view, cell, store, i, data):
		img = store.get_value(i, 0)
		cell.props.pixbuf = img

	def on_drag_data_get(self, widget, drag_context, data, info, time):
		selected_path = self._iconview.get_selected_items()[0]
		selected_iter = self._iconstore.get_iter(selected_path)

		i = self._iconstore.get_value(selected_iter, 1)
		text = "![Alt. Text][{}]".format(i)
		data.set_text(text+chr(0), -1)

	def get_text(self):
		text = self._sourcebuffer.get_text(
					self._sourcebuffer.get_start_iter(),
					self._sourcebuffer.get_end_iter(),
					True)
		text += "\n" + INTO_DEFS_CONSTANT + "\n"
		for i in self._iconstore:
			text += "[{}]: {} \"{}\"".format(i[1], i[2], i[1])
		return text

	def set_text(self, text):
		pos = text.rfind(INTO_DEFS_CONSTANT)
		text = text[:pos]
		self._sourcebuffer.set_text(text+chr(0))

	def load_resources(self, file_text):
		for line in file_text.splitlines():
			title, name = line.split(',')
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
					os.path.join(self._activity.path, name),
					200, -1, True)
			self._iconstore.append([pixbuf, str(UID), name])

	def save_resources(self):
		"""Returns a list of files and a text file to be saved"""
		to_save = []
		data_file = ""
		for i in self._iconstore:
			to_save.append(i[2])
			data_file += "{},{}".format(i[1], i[2])
		return to_save, data_file.strip()

class SourceViewDrop(GtkSource.View):
	def __init__(self, buffer_):
		GtkSource.View.__init__(self, buffer=buffer_)

		self.drag_dest_set(Gtk.DestDefaults.ALL, [],
						 Gdk.DragAction.COPY)
		self.connect("drag-data-received", self.on_drag_data_received)
		self.drag_source_add_text_targets()

	def on_drag_data_received(self, widget, drag_context, x, y,
					 data, info, time):
		#pos, trailing = self.get_iter_at_position(x, y)
		buffer_ = self.get_buffer()
		buffer_.insert_at_courser(data.get_text())
