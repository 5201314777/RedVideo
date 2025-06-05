from qtpy import QtGui, QtWidgets


def newAction(parent,text,slot=None,checkable=None,enabled=True, checked=False):
    action=QtGui.QAction(text,parent)
    if slot is not None:
        action.triggered.connect(slot)
    if checkable is not None:
        action.setChecked(True)
    action.setEnabled(enabled)
    action.setChecked(checked)
    return action
def addActions(widget, actions):
    for action in actions:
        if action is None:
            widget.addSeparator()
        elif isinstance(action, QtWidgets.QMenu):
            widget.addMenu(action)
        else:
            widget.addAction(action)
class struct(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)