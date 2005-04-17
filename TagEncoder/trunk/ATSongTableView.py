from PyObjCTools import NibClassBuilder, AppHelper
from Foundation import *
from AppKit import *

class ATSongTableView(NibClassBuilder.AutoBaseClass):
    
    isEditing = False
    
    def awakeFromNib(self):
        self.isEditing = False
        pass

    def draggingSourceOperationMaskForLocal_(self, isLocal):
        if not isLocal:
            return NSDragOperationGeneric|NSDragOperationCopy
        else:
            return NSDragOperationNone

    def textDidBeginEditing_(self, aNotification):
        self.isEditing = True
        super(ATSongTableView, self).textDidBeginEditing_(aNotification)        
        
    def textDidEndEditing_(self, aNotification):
        self.isEditing = False        
        super(ATSongTableView, self).textDidEndEditing_(aNotification)

    def keyUp_(self, theEvent):
        if not self.isEditing and theEvent.keyCode() == 51:
            self.dataSource().deleteRows(self.selectedRowIndexes())
        super(ATSongTableView, self).keyUp_(theEvent)            
        
    def menuForEvent_(self, theEvent):
        # figure out which row/column we clicked
        point = self.convertPoint_fromView_(theEvent.locationInWindow(), None)
        col = self.columnAtPoint_(point)
        row = self.rowAtPoint_(point)
        
        if row == -1 or col == -1:
            return None
        elif self.tableColumns()[col].identifier() == 'fname':
            return None
        else:
            # get menu for row,col combination
            prefs = self.dataSource().mainController.prefsControl
            encs = prefs.enabledEncodings
            enc_used = self.dataSource().encodingUsedForRow_column_(row, col)
            
            # create menu by removing all old fields
            # and attaching new one
            defaultMenu = super(ATSongTableView, self).menu()
            while defaultMenu.numberOfItems() > 2:
                defaultMenu.removeItemAtIndex_(2)
            defaultMenu.itemAtIndex_(0).setEnabled_(False)
            
            for e in encs:
                menuItem = \
                    NSMenuItem.alloc().initWithTitle_action_keyEquivalent_( \
                    e, "changeEncoding:", "")
                menuItem.setTarget_(self.dataSource())
                menuItem.setRepresentedObject_([e, row, col])
                menuItem.setEnabled_(True)
                if enc_used == e:
                    menuItem.setState_(True)
                defaultMenu.addItem_(menuItem)
            return defaultMenu
            
    """ This is for Drag and Drop with Promised Files
    def namesOfPromisedFilesDroppedAtDestination_(self, destination):
        # - (NSArray *)namesOfPromisedFilesDroppedAtDestination:
        #           (NSURL *)dropDestination
        self.dataSource().namesOfPromisedFilesDroppedAtDestination_(destination)
    """ 