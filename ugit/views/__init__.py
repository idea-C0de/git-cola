import os
import time
from PyQt4 import QtCore
from PyQt4.QtGui import QDialog
from PyQt4.QtGui import QMainWindow
from PyQt4.QtGui import QCheckBox
from PyQt4.QtGui import QSplitter

from ugit import qtutils
from ugit.syntax import DiffSyntaxHighlighter
from ugit.syntax import LogSyntaxHighlighter

from main import Ui_main
from remote import Ui_remote
from branch import Ui_branch
from commit import Ui_commit
from logger import Ui_logger
from search import Ui_search
from options import Ui_options
from createbranch import Ui_createbranch
from merge import Ui_merge
from bookmark import Ui_bookmark
from stash import Ui_stash

def CreateStandardView(uiclass, qtclass):
	"""CreateStandardView returns a class closure of uiclass and qtclass.
	This class performs the standard setup common to all view classes."""
	class StandardView(uiclass, qtclass):
		def __init__(self, parent=None, *args, **kwargs):
			qtclass.__init__(self, parent)
			uiclass.__init__(self)
			self.parent_view = parent
			self.setupUi(self)
			self.init(parent, *args, **kwargs)
		def init(self, parent, *args, **kwargs):
			pass
	return StandardView

class View(CreateStandardView(Ui_main, QMainWindow)):
	'''The main ugit interface.'''
	def init(self, parent=None):
		self.staged.setAlternatingRowColors(True)
		self.unstaged.setAlternatingRowColors(True)
		self.set_display = self.display_text.setText
		self.set_info = self.displayLabel.setText
		self.action_undo = self.commitmsg.undo
		self.action_redo = self.commitmsg.redo
		self.action_paste = self.commitmsg.paste
		self.action_select_all = self.commitmsg.selectAll

		# Handle automatically setting the horizontal/vertical orientation
		self.splitter.resizeEvent = self.splitter_resize_event

		# Qt does not support noun/verbs
		self.commit_button.setText(qtutils.tr('Commit@@verb'))
		self.commit_menu.setTitle(qtutils.tr('Commit@@verb'))
		# Default to creating a new commit(i.e. not an amend commit)
		self.new_commit_radio.setChecked(True)
		self.toolbar_show_log = self.toolbar.addAction(
				qtutils.get_qicon('git.png'),
				'Show/Hide Log Window')
		self.toolbar_show_log.setEnabled(True)

		# Setup the default dock layout
		self.tabifyDockWidget(self.diff_dock, self.editor_dock)

		dock_area = QtCore.Qt.TopDockWidgetArea
		self.addDockWidget(dock_area, self.status_dock)

		toolbar_area = QtCore.Qt.BottomToolBarArea
		self.addToolBar(toolbar_area, self.toolbar)

		# Diff/patch syntax highlighter
		DiffSyntaxHighlighter(self.display_text.document())

	def splitter_resize_event(self, event):
		width = self.splitter.width()
		height = self.splitter.height()
		if width > height:
			self.splitter.setOrientation(QtCore.Qt.Horizontal)
		else:
			self.splitter.setOrientation(QtCore.Qt.Vertical)
		QSplitter.resizeEvent(self.splitter, event)

	def action_cut(self):
		self.action_copy()
		self.action_delete()
	def action_copy(self):
		cursor = self.commitmsg.textCursor()
		selection = cursor.selection().toPlainText()
		qtutils.set_clipboard(selection)
	def action_delete(self):
		self.commitmsg.textCursor().removeSelectedText()
	def reset_display(self):
		self.set_display('')
		self.set_info('')
	def copy_display(self):
		cursor = self.display_text.textCursor()
		selection = cursor.selection().toPlainText()
		qtutils.set_clipboard(selection)
	def diff_selection(self):
		cursor = self.display_text.textCursor()
		offset = cursor.position()
		selection = cursor.selection().toPlainText()
		num_selected_lines = selection.count('\n')
		return offset, selection
	def display(self, text):
		self.set_display(text)
		self.diff_dock.raise_()

class LogView(CreateStandardView(Ui_logger, QDialog)):
	'''A simple dialog to display command logs.'''
	def init(self, parent=None, output=None):
		self.setWindowTitle(self.tr('Git Command Log'))
		LogSyntaxHighlighter(self.output_text.document())
		if output:
			self.set_output(output)
	def clear(self):
		self.output_text.clear()
	def set_output(self, output):
		self.output_text.setText(output)
	def log(self, output):
		if not output: return
		cursor = self.output_text.textCursor()
		cursor.movePosition(cursor.End)
		text = self.output_text
		cursor.insertText(time.asctime() + '\n')
		for line in unicode(output).splitlines():
			cursor.insertText(line + '\n')
		cursor.insertText('\n')
		cursor.movePosition(cursor.End)
		text.setTextCursor(cursor)

class BranchView(CreateStandardView(Ui_branch, QDialog)):
	'''A dialog for choosing branches.'''
	def init(self, parent, branches):
		self.reset()
		if branches:
			self.add(branches)
	def reset(self):
		self.branches = []
		self.branch_combo.clear()
	def add(self, branches):
		for branch in branches:
			self.branches.append(branch)
			self.branch_combo.addItem(branch)
	def get_selected(self):
		self.show()
		if self.exec_() == QDialog.Accepted:
			return self.branches[self.branch_combo.currentIndex()]
		else:
			return None

class CommitView(CreateStandardView(Ui_commit, QDialog)):
	def init(self, parent=None, title=None):
 		if title: self.setWindowTitle(title)
 		# Make the list widget slighty larger
 		self.splitter.setSizes([ 50, 200 ])
 		DiffSyntaxHighlighter(self.commit_text.document(),
 				whitespace=False)

class SearchView(CreateStandardView(Ui_search, QDialog)):
	def init(self, parent=None):
		self.input.setFocus()
		DiffSyntaxHighlighter(self.commit_text.document(),
				whitespace=False)

class MergeView(CreateStandardView(Ui_merge, QDialog)):
	def init(self, parent=None):
		self.revision.setFocus()

class RemoteView(CreateStandardView(Ui_remote, QDialog)):
	def init(self, parent=None, button_text=''):
		if button_text:
			self.action_button.setText(button_text)
			self.setWindowTitle(button_text)
	def select_first_remote(self):
		item = self.remotes.item(0)
		if item:
			self.remotes.setItemSelected(item, True)
			self.remotes.setCurrentItem(item)
			self.remotename.setText(item.text())
			return True
		else:
			return False

# These are views that do not contain any custom methods
CreateBranchView = CreateStandardView(Ui_createbranch, QDialog)
OptionsView = CreateStandardView(Ui_options, QDialog)
BookmarkView = CreateStandardView(Ui_bookmark, QDialog)
StashView = CreateStandardView(Ui_stash, QDialog)
