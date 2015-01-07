#
#  Project: MXCuBE
#  https://github.com/mxcube.
#
#  This file is part of MXCuBE software.
#
#  MXCuBE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  MXCuBE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

from PyQt4 import QtGui
from PyQt4 import QtCore 

from BlissFramework import Qt4_Icons
from BlissFramework.Utils import Qt4_widget_colors
from BlissFramework.Qt4_BaseComponents import BlissWidget

__category__ = "Qt4_General"

class Qt4_EnergyBrick(BlissWidget):
    """
    Descript. : EnergyBrick displays actual energy and wavelength.
    """
    def __init__(self, *args):
        """
        Descript. : Initiates BlissWidget Brick
        """
        BlissWidget.__init__(self, *args)

        # Hardware objects ----------------------------------------------------
        self.energy_hwobj = None

        # Internal values -----------------------------------------------------
        self.energy_limits = None
        self.wavelength_limits = None

        # Properties ----------------------------------------------------------       
        self.addProperty('mnemonic', 'string', '')
        self.addProperty('defaultMode', 'combo', ('keV', 'Ang'), 'keV')
        self.addProperty('kevFormatString', 'formatString', '###.####')
        self.addProperty('angFormatString', 'formatString', '##.###')

        # Signals ------------------------------------------------------------

        # Slots ---------------------------------------------------------------

        # Graphic elements ----------------------------------------------------
        self.main_frame = QtGui.QFrame(self)
        self.main_frame.setFrameStyle(QtGui.QFrame.StyledPanel)
        self.group_box = QtGui.QGroupBox("Energy", self.main_frame)
        energy_label = QtGui.QLabel("Current:", self.group_box)
        energy_label.setFixedWidth(75)
        wavelength_label = QtGui.QLabel("Wavelength: ", self.group_box)
        self.energy_ledit = QtGui.QLineEdit(self.group_box)
        self.energy_ledit.setReadOnly(True)
        self.wavelength_ledit = QtGui.QLineEdit(self.group_box)
        self.wavelength_ledit.setReadOnly(True)

        self.new_value_widget = QtGui.QWidget(self)
        set_to_label = QtGui.QLabel("Set to: ", self)
        self.new_value_ledit = QtGui.QLineEdit(self.new_value_widget)
        self.units_combobox = QtGui.QComboBox(self.new_value_widget)
        self.units_combobox.addItems(["keV", chr(197)]) 
        self.stop_button = QtGui.QPushButton(self.new_value_widget)        
        self.stop_button.setIcon(QtGui.QIcon(Qt4_Icons.load("Stop2")))
        self.stop_button.setEnabled(False)
 
        # Layout --------------------------------------------------------------
        self.new_value_widget_layout = QtGui.QHBoxLayout(self)
        self.new_value_widget_layout.addWidget(self.new_value_ledit)
        self.new_value_widget_layout.addWidget(self.units_combobox)
        self.new_value_widget_layout.addWidget(self.stop_button)
        self.new_value_widget_layout.setSpacing(0)
        self.new_value_widget_layout.setContentsMargins(0, 0, 0, 0)
        self.new_value_widget.setLayout(self.new_value_widget_layout) 

        self.group_box_layout = QtGui.QGridLayout()
        self.group_box_layout.addWidget(energy_label, 0, 0)
        self.group_box_layout.addWidget(self.energy_ledit, 0, 1) 
        self.group_box_layout.addWidget(wavelength_label, 1, 0)
        self.group_box_layout.addWidget(self.wavelength_ledit, 1, 1)
        self.group_box_layout.addWidget(set_to_label, 2, 0) 
        self.group_box_layout.addWidget(self.new_value_widget, 2, 1)
        self.group_box_layout.setSpacing(0)
        self.group_box_layout.setContentsMargins(1, 1, 1, 1) 
        self.group_box.setLayout(self.group_box_layout)

        self.main_frame_layout = QtGui.QVBoxLayout() 
        self.main_frame_layout.setSpacing(0)
        self.main_frame_layout.setContentsMargins(0, 0, 0, 0)
        self.main_frame_layout.addWidget(self.group_box)
        self.main_frame.setLayout(self.main_frame_layout)   

        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 2, 2)
        self.main_layout.addWidget(self.main_frame)
        self.setLayout(self.main_layout)

        # SizePolicies --------------------------------------------------------
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, 
                           QtGui.QSizePolicy.Fixed)

        # Qt signal/slot connections ------------------------------------------
        self.connect(self.new_value_ledit, QtCore.SIGNAL("returnPressed()"), self.current_value_changed)
        self.connect(self.new_value_ledit, QtCore.SIGNAL("textChanged(const QString &)"), self.input_field_changed)
        self.connect(self.units_combobox, QtCore.SIGNAL("activated(const QString &)"), self.units_changed)
        self.connect(self.stop_button, QtCore.SIGNAL("clicked()"), self.stop_clicked)

        # Other --------------------------------------------------------------- 
        self.group_box.setCheckable(True)
        self.group_box.setChecked(True)
        Qt4_widget_colors.set_widget_color(self.new_value_ledit, 
                                       Qt4_widget_colors.LINE_EDIT_ACTIVE,
                                       QtGui.QPalette.Base)
        self.new_value_validator = QtGui.QDoubleValidator(self.new_value_ledit)

    def propertyChanged(self, property_name, old_value, new_value):
        """
        Descript. : Event triggered when user property changed in the property
                    editor. 
        Args.     : property_name (string), old_value, new_value
        Return.   : None
        """
        if property_name == 'mnemonic':
            if self.energy_hwobj is not None:
                self.disconnect(self.energy_hwobj, QtCore.SIGNAL('deviceReady'), self.connected)
                self.disconnect(self.energy_hwobj, QtCore.SIGNAL('deviceNotReady'), self.disconnected)
                self.disconnect(self.energy_hwobj, QtCore.SIGNAL('energyChanged'), self.energy_changed)

            self.energy_hwobj = self.getHardwareObject(new_value)
            if self.energy_hwobj is not None:
                self.set_new_value_limits()
                self.connect(self.energy_hwobj, QtCore.SIGNAL('deviceReady'), self.connected)
                self.connect(self.energy_hwobj, QtCore.SIGNAL('deviceNotReady'), self.disconnected)
                self.connect(self.energy_hwobj, QtCore.SIGNAL('energyChanged'), self.energy_changed)
                
                if self.energy_hwobj.isReady():
                    self.connected()
                else:
                    self.disconnected()
            else:
                self.disconnected()
        elif property_name == 'defaultMode':
            if new_value == "keV":
                self.units_combobox.setCurrentIndex(0)
            else:
                self.units_combobox.setCurrentIndex(1)

        elif property_name == 'alwaysReadonly':
            pass
        else:
            BlissWidget.propertyChanged(self, property_name, old_value, new_value)

    def connected(self):
        """
        Descript. :
        Args.     :
        Return.   : 
        """
        self.setEnabled(True)
        tunable_energy = self.energy_hwobj.can_move_energy()
        if tunable_energy is None:
            tunable_energy = False 
        self.new_value_ledit.setEnabled(tunable_energy)
        self.units_combobox.setEnabled(tunable_energy)

    def disconnected(self):
        """
        Descript. :
        Args.     :
        Return.   : 
        """
        self.setEnabled(False)

    def energy_changed(self, energy_value, wavelength_value):
        """
        Descript. :
        Args.     :
        Return.   : 
        """
        energy_value_str = self['kevFormatString'] % energy_value
        wavelength_value_str = self['angFormatString'] % wavelength_value
        
        self.energy_ledit.setText("%s keV" % energy_value_str)
        self.wavelength_ledit.setText("%s %s" %(wavelength_value, chr(197)))

    def current_value_changed(self):
        """
        Descript. :
        Args.     :
        Return.   : 
        """
        self.energy_hwobj.move_energy(float(self.new_value_ledit.text()))

    def input_field_changed(self, input_field_text):
        """
        Descript. :
        Args.     :
        Return.   : 
        """
        Qt4_widget_colors.set_widget_color(self.new_value_ledit, 
                                       Qt4_widget_colors.LINE_EDIT_CHANGED,
                                       QtGui.QPalette.Base)
        print self.new_value_ledit.validator().validate(input_field_text, 0)

    def units_changed(self, unit):
        """
        Descript. :
        Args.     :
        Return.   : 
        """
        self.set_new_value_limits()

    def set_new_value_limits(self):
        """
        Descript. :
        Args.     :
        Return.   : 
        """
        value_limits = [0, 10]
        if self.units_combobox.currentIndex() == 0:
            value_limits = self.energy_hwobj.get_energy_limits()
            tool_tip = "Energy limits" 
        else:
            value_limits = self.energy_hwobj.get_wavelength_limits()
            tool_tip = "Wavelength limits"
        if value_limits is not None:
            self.new_value_validator.setRange(value_limits[0], value_limits[1], 2)    
            self.new_value_ledit.setValidator(self.new_value_validator)
            self.new_value_ledit.setToolTip("%s : %s" %(tool_tip, value_limits))
   
    def stop_clicked(self):
        """
        Descript. :
        Args.     :
        Return.   : 
        """
        print "stoped clicked"

