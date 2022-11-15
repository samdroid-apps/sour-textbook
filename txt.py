import logging
import os
import tarfile
import markdown

from gi.repository import Gtk
from gi.repository import WebKit

from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarButton	
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton

from markdown_edit_view import markdownEditView

DEFAULT_MARKDOWN = """
Let's make a textbook
---------------------
"""
HTML_WRAPPER = """
<html><body>%s</body></html>
"""

VIEW_VIEW = 0
VIEW_EDIT = 1

class TextBookActivity(activity.Activity):
	
	def __init__(self, handle):	
		super(TextBookActivity, self).__init__(handle)
		
		self.path = os.path.join(self.get_activity_root(), "tmp")
		self._markdown = DEFAULT_MARKDOWN
		self._html = ''
		self._webview = None
		self._markdownEditView = markdownEditView(self._markdown, self)

		self._current_view = VIEW_VIEW
		self._setup_current_view()

		self._setup_toolbar()

	def read_file(self, path):
		with tarfile.open(path) as tar:
def is_within_directory(directory, target):
	
	abs_directory = os.path.abspath(directory)
	abs_target = os.path.abspath(target)

	prefix = os.path.commonprefix([abs_directory, abs_target])
	
	return prefix == abs_directory

def safe_extract(tar, path=".", members=None, *, numeric_owner=False):

	for member in tar.getmembers():
		member_path = os.path.join(path, member.name)
		if not is_within_directory(path, member_path):
			raise Exception("Attempted Path Traversal in Tar File")

	tar.extractall(path, members, numeric_owner=numeric_owner) 
	

safe_extract(tar, self.path)

		with open(os.path.join(self.path, 'raw.md')) as f:
			self._markdown = f.read()
		self._markdownEditView.set_text(self._markdown)
		self._setup_current_view()

		with open(os.path.join(self.path, 'res.almost.csv')) as f:
			text = f.read().strip()
			self._markdownEditView.load_resources(text)

	def write_file(self, path):
		#First we update the files in the tmp directoy
		if self._current_view == VIEW_EDIT:
			self._markdown = self._markdownEditView.get_text()
		with open(os.path.join(self.path, 'raw.md'), 'w') as f:
			f.write(self._markdown)

		resList, resCsv = self._markdownEditView.save_resources()
		with open(os.path.join(self.path, 'res.almost.csv'), 'w') as f:
			f.write(resCsv)

		#They tar 'em up scotty
		with tarfile.open(path, 'w') as tar:
			for file_ in ['raw.md', 'res.almost.csv'] + resList:
				tar.add(os.path.join(self.path, file_), file_)

	def _setup_current_view(self):
		f = {VIEW_VIEW: self._setup_view_view,
			VIEW_EDIT: self._setup_view_edit}[self._current_view]
		f()

	def _render_markdown(self):
		self._markdown = self._markdownEditView.get_text()
		self._html = markdown.markdown(self._markdown)
		self._html = HTML_WRAPPER % self._html
		
	def _setup_view_view(self):
		if not self._webview:
			self._webview = WebKit.WebView.new()

		self._render_markdown()
		self._webview.load_string(self._html, "text/html", "UTF-8",
							"file://" + self.path)

		self.set_canvas(self._webview)
		self._webview.show()

	def _setup_view_edit(self):
		self._markdownEditView.set_text(self._markdown)
		self.set_canvas(self._markdownEditView)
		self._markdownEditView.show()

	def _setup_toolbar(self):
		self._toolbar_box = ToolbarBox()
		activity_button = ActivityToolbarButton(self)
		self._toolbar_box.toolbar.insert(activity_button, 0)
		self.set_toolbar_box(self._toolbar_box)
		self._toolbar = self.get_toolbar_box().toolbar
		
		control_view = Gtk.ToolButton.new_from_stock('gtk-justify-center')
		control_view.connect("clicked", self._change_view_view)
		self._toolbar.insert(control_view, -1)
		
		control_edit = Gtk.ToolButton.new_from_stock('gtk-select-color')
		control_edit.connect("clicked", self._change_view_edit)
		self._toolbar.insert(control_edit, -1)
		
		separator = Gtk.SeparatorToolItem()
		separator.props.draw = False
		separator.set_expand(True)
		self._toolbar.insert(separator, -1)
		self._toolbar.insert(StopButton(self), -1)
		self.get_toolbar_box().show_all()

	def _change_view_view(self, callingView):
		self._current_view = VIEW_VIEW
		self._setup_current_view()

	def _change_view_edit(self, callingView):
		self._current_view = VIEW_EDIT
		self._setup_current_view()
