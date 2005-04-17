from PyObjCTools import NibClassBuilder, AppHelper
from Foundation import *
from AppKit import *

NibClassBuilder.extractClasses("MainMenu")

from ATMainController import ATMainController
from ATSongTableController import ATSongTableController
from ATSongTableView import ATSongTableView
from ATEncodingPrefsController import ATEncodingPrefsController
from ATDragDropTableView import ATDragDropTableView

if __name__ == "__main__":
        AppHelper.runEventLoop()