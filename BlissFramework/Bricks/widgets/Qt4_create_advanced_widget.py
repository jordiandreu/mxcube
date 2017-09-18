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

import os
import logging
#from copy import deepcopy

from QtImport import *

import Qt4_queue_item
import Qt4_GraphicsManager
import queue_model_objects_v1 as queue_model_objects

from Qt4_create_task_base import CreateTaskBase
from widgets.Qt4_data_path_widget import DataPathWidget
from widgets.Qt4_acquisition_widget import AcquisitionWidget
from queue_model_enumerables_v1 import EXPERIMENT_TYPE


class CreateAdvancedWidget(CreateTaskBase):
    """Widget used to create advanced collection methods
    """

    def __init__(self, parent=None,name=None, fl=0):
        CreateTaskBase.__init__(self, parent, name, 
            Qt.WindowFlags(fl), 'Advanced')

        if not name:
            self.setObjectName("create_advanced_widget")

        # Hardware objects ----------------------------------------------------
 
        # Internal variables --------------------------------------------------
        self.init_models()
        self._advanced_methods = None
        self._grid_map = {}
        self.spacing = [0, 0]

        # Graphic elements ----------------------------------------------------
        self._advanced_methods_widget = loadUi(os.path.join(\
            os.path.dirname(__file__), "ui_files/Qt4_advanced_methods_layout.ui"))

        self._acq_widget =  AcquisitionWidget(self, "acquisition_widget",
             layout='vertical', acq_params=self._acquisition_parameters,
             path_template=self._path_template)
        self._acq_widget.grid_mode = True

        self._data_path_widget = DataPathWidget(self, 'create_dc_path_widget', 
             data_model = self._path_template, layout = 'vertical')

        # Layout --------------------------------------------------------------
        _main_vlayout = QVBoxLayout(self) 
        _main_vlayout.addWidget(self._advanced_methods_widget)
        _main_vlayout.addWidget(self._acq_widget)
        _main_vlayout.addWidget(self._data_path_widget)
        _main_vlayout.addStretch(0)
        _main_vlayout.setSpacing(2)
        _main_vlayout.setContentsMargins(2, 2, 2, 2)

        # SizePolicies --------------------------------------------------------

        # Qt signal/slot connections ------------------------------------------
        self._acq_widget.acqParametersChangedSignal.\
             connect(self.acq_parameters_changed)
        self._acq_widget.madEnergySelectedSignal.\
             connect(self.mad_energy_selected)

        self._acq_widget.acq_widget_layout.osc_range_ledit.textEdited.connect(\
             self.grid_osc_range_ledit_changed)
        self._acq_widget.acq_widget_layout.osc_total_range_ledit.textEdited.connect(\
             self.grid_osc_total_range_ledit_changed)
        self._acq_widget.acq_widget_layout.set_max_osc_range_button.clicked.\
             connect(self.set_max_osc_total_range_clicked)

        self._data_path_widget.pathTemplateChangedSignal.\
             connect(self.path_template_changed)

        self._advanced_methods_widget.grid_treewidget.itemSelectionChanged.\
             connect(self.grid_treewidget_item_selection_changed)
        self._advanced_methods_widget.draw_grid_button.clicked.\
             connect(self.draw_grid_button_clicked)
        self._advanced_methods_widget.remove_grid_button.clicked.\
             connect(self.remove_grid_button_clicked)
        self._advanced_methods_widget.hor_spacing_ledit.textEdited.\
             connect(self.hor_spacing_changed)
        self._advanced_methods_widget.ver_spacing_ledit.textEdited.\
             connect(self.ver_spacing_changed)

        self._advanced_methods_widget.move_right_button.clicked.\
             connect(lambda : self.move_grid("right"))
        self._advanced_methods_widget.move_left_button.clicked.\
             connect(lambda : self.move_grid("left"))
        self._advanced_methods_widget.move_up_button.clicked.\
             connect(lambda : self.move_grid("up"))
        self._advanced_methods_widget.move_down_button.clicked.\
             connect(lambda : self.move_grid("down"))        
      
        self._advanced_methods_widget.overlay_cbox.toggled.\
             connect(self.overlay_toggled)
        self._advanced_methods_widget.overlay_slider.valueChanged.\
             connect(self.overlay_alpha_changed) 
        self._advanced_methods_widget.overlay_color_button.clicked.\
             connect(self.overlay_change_color)
        self._advanced_methods_widget.move_to_grid_button.clicked.\
             connect(self.move_to_grid)

        # Other ---------------------------------------------------------------
        self._acq_widget.use_osc_start(False)
        self._acq_widget.use_kappa(False) 
        self._acq_widget.acq_widget_layout.num_images_label.setEnabled(False)
        self._acq_widget.acq_widget_layout.num_images_ledit.setEnabled(False)
        for col in range(self._advanced_methods_widget.\
                         grid_treewidget.columnCount()):
            self._advanced_methods_widget.grid_treewidget.\
                 resizeColumnToContents(col)

        self._acq_widget.acq_widget_layout.osc_total_range_label.setText(\
            "Total osc. range per line")

    def init_models(self):
        """
        Descript. :
        """
        CreateTaskBase.init_models(self)
        self._init_models()

    def _init_models(self):
        """
        Descript. :
        """
        CreateTaskBase.init_models(self)
        self._processing_parameters = queue_model_objects.ProcessingParameters()

        if self._beamline_setup_hwobj is not None:
            has_shutter_less = self._beamline_setup_hwobj.\
                               detector_has_shutterless()
            self._acquisition_parameters.shutterless = has_shutter_less

            self._acquisition_parameters = self._beamline_setup_hwobj.\
                get_default_acquisition_parameters("default_advanced_values")

            if not self._advanced_methods:
                self._advanced_methods = self._beamline_setup_hwobj.get_advanced_methods()            
                if self._advanced_methods:
                   for method in self._advanced_methods:
                       self._advanced_methods_widget.method_combo.addItem(method)
                else:
                   self.setEnabled(False)    

            self.grid_treewidget_item_selection_changed()

    def set_beamline_setup(self, bl_setup_hwobj):
        """
        In plate mode osciallation is start is in the middle of grid
        """
        CreateTaskBase.set_beamline_setup(self, bl_setup_hwobj)

        self._acq_widget.acq_widget_layout.osc_start_label.\
             setText("Oscillation middle:")
        self._acq_widget.acq_widget_layout.\
             set_max_osc_range_button.setEnabled(False)

        hor_size, ver_size = bl_setup_hwobj.beam_info_hwobj.get_beam_size()
        self.spacing = [hor_size, ver_size] 
        self._advanced_methods_widget.hor_spacing_ledit.setText("%.1f" % (hor_size * 1000))
        self._advanced_methods_widget.ver_spacing_ledit.setText("%.1f" % (ver_size * 1000))

    def approve_creation(self):
        """
        Descript. :
        """
        result = CreateTaskBase.approve_creation(self)
        selected_grid = self.get_selected_grid()

        if not selected_grid:
            msg = "No grid selected. Please select a grid to continue!"
            logging.getLogger("GUI").warning(msg)
            result = False
        else:
            grid_properties = selected_grid.get_properties()
            exp_time = float(self._acq_widget.acq_widget_layout.exp_time_ledit.text())
            speed = grid_properties["yOffset"] / exp_time
            print speed
            if speed >= 0.8:
                logging.getLogger("GUI").error("Translation speed %.3f is above the limit 0.8" % speed)
                return False
            osc_range_per_frame = float(self._acq_widget.acq_widget_layout.osc_range_ledit.text())
            speed = osc_range_per_frame / exp_time
            print speed
            if speed >= 166:
                logging.getLogger("GUI").error("Rotation speed per frame %.3f is above the limit 166" % speed)
                return False
            result = True

        return result
            
    def update_processing_parameters(self, crystal):
        """
        Descript. :
        """
        return

    def single_item_selection(self, tree_item):
        """
        Descript. :
        """
        CreateTaskBase.single_item_selection(self, tree_item)
        if isinstance(tree_item, Qt4_queue_item.SampleQueueItem):
            pass
            #self._init_models()
            ##self._acq_widget.update_data_model(self._acquisition_parameters,
            #                                    self._path_template)            
        elif isinstance(tree_item, Qt4_queue_item.BasketQueueItem):
            self.setDisabled(False)
        elif isinstance(tree_item, Qt4_queue_item.DataCollectionQueueItem) or \
             isinstance(tree_item, Qt4_queue_item.XrayCenteringQueueItem):

            if isinstance(tree_item, Qt4_queue_item.XrayCenteringQueueItem):
                data_collection = tree_item.get_model().reference_image_collection                 
            else:
                data_collection = tree_item.get_model()

            if tree_item.get_model().is_executed():
                self.setDisabled(True)
            else:
                self.setDisabled(False)

            if data_collection.is_mesh():
                # sample_data_model = self.get_sample_item(tree_item).get_model()
                #self._acq_widget.disable_inverse_beam(True)
                #self._graphics_manager_hwobj.de_select_all()
                self._graphics_manager_hwobj.select_shape(data_collection.grid)

                self._path_template = data_collection.get_path_template()
                self._data_path_widget.update_data_model(self._path_template)

                self._acquisition_parameters = data_collection.acquisitions[0].\
                                              acquisition_parameters
                self._acq_widget.update_data_model(self._acquisition_parameters,
                                                   self._path_template)
                self.get_acquisition_widget().use_osc_start(True)
        else:
            self.setDisabled(True)
        self.grid_treewidget_item_selection_changed()
  
    def _create_task(self,  sample, shape):
        """Creates tasks based on selected grids

        :param sample: selected sample object
        :type sample: SampleQueueItem
        :param shape: selected shape
        :type shape: Qt4_GraphicsLib.GraphicsItem
        """
        tasks = []
        selected_grid = self.get_selected_grid()
        mesh_dc = self._create_dc_from_grid(sample, selected_grid)

        exp_type = str(self._advanced_methods_widget.method_combo.currentText())
        if exp_type == "MeshScan":
            tasks.append(mesh_dc)
        elif exp_type == "XrayCentering":
            xray_centering = queue_model_objects.XrayCentering(mesh_dc)
            tasks.append(xray_centering)
        mesh_dc.run_processing_parallel = exp_type

        return tasks

    def shape_created(self, shape, shape_type):
        """If a grid is created then adds it to the treewidget.
           A binding between graphical grid and treewidget item is based
           on the self._grid_map

        :param shape: graphics object
        :type shape: Qt4_GraphicsLib.GraphicsItem
        :param shape_type: type of the object (point, line, grid)
        :type shape_type: str 
        """
        if shape_type == "Grid":
            self._advanced_methods_widget.grid_treewidget.clearSelection()
            grid_properties = shape.get_properties()
            info_str_list = []
            info_str_list.append(grid_properties["name"])
            #info_str_list.append("%d" % (grid_properties["beam_x_mm"] * 1000.0))
            #info_str_list.append("%d" % (grid_properties["beam_y_mm"] * 1000.0))
            info_str_list.append("%d" % grid_properties["num_lines"])
            info_str_list.append("%d" % grid_properties["num_images_per_line"])

            exp_time = max(float(grid_properties["yOffset"] / 0.8),
                               self._acq_widget.exp_time_validator.bottom()+0.00001)
            self._acq_widget.acq_widget_layout.exp_time_ledit.setText("%.6f" % exp_time)

            grid_treewidget_item = QTreeWidgetItem(\
                self._advanced_methods_widget.grid_treewidget,
                info_str_list)
            grid_treewidget_item.setSelected(True)
            self._grid_map[shape] = grid_treewidget_item
            self.grid_treewidget_item_selection_changed()
            self.update_grid_osc_total_range()

            
            
    def shape_deleted(self, shape, shape_type):
        """Removes shape from QTreeWidget and self._grid_map

        :param shape: graphics object
        :type shape: QtGraphicsLib.GraphicsItem
        :param shape_type: type of the object (point, line, grid)
        :type shape_type: str 
        """
        if self._grid_map.get(shape):
            treewidget_item_modelindex = self._advanced_methods_widget.\
                 grid_treewidget.indexFromItem(self._grid_map[shape])
            self._advanced_methods_widget.grid_treewidget.takeTopLevelItem(\
                 treewidget_item_modelindex.row())
            self._grid_map.pop(shape) 

    def grid_treewidget_item_selection_changed(self):
        """Updates acquisition parameters based on the selected grid.
        """
        self.enable_grid_controls(False)
      
        osc_dynamic_limits = None

        #if self._beamline_setup_hwobj.diffractometer_hwobj.in_plate_mode():
        #    osc_dynamic_limits = self._beamline_setup_hwobj.\
        #        diffractometer_hwobj.get_osc_dynamic_limits()

        for item in self._grid_map.items():
            grid = item[0]
            treewidget_item = item[1]
  
            if treewidget_item.isSelected():
                grid_properties = grid.get_properties() 
                cell_count = grid_properties["num_lines"] * \
                             grid_properties["num_images_per_line"]
                self._acq_widget.acq_widget_layout.num_images_ledit.setText(\
                     "%d" % cell_count)
                self._acq_widget.acq_widget_layout.first_image_ledit.setText(\
                     "%d" % grid_properties["first_image_num"])
                centred_point = grid.get_centred_position()
                #self._acq_widget.acq_widget_layout.osc_start_ledit.setText(\
                #     "%.2f" % float(centred_point.phi))
                self._acq_widget.acq_widget_layout.kappa_ledit.setText(\
                     "%.2f" % float(centred_point.kappa))
                self._acq_widget.acq_widget_layout.kappa_phi_ledit.setText(\
                     "%.2f" % float(centred_point.kappa_phi))
                self._advanced_methods_widget.hor_spacing_ledit.setText(\
                     "%.2f" % (float(grid_properties["xOffset"]) * 1000))
                self._advanced_methods_widget.ver_spacing_ledit.setText(\
                     "%.2f" % (float(grid_properties["yOffset"]) * 1000))

                treewidget_item.setText(3, str(grid_properties["num_lines"]))
                treewidget_item.setText(4, str(grid_properties["num_images_per_line"]))
            
                #exp_time = max(float(grid_properties["yOffset"] / 0.8),
                #               self._acq_widget.exp_time_validator.bottom())
                #self._acq_widget.acq_widget_layout.exp_time_ledit.setText("%.6f" % exp_time)
                """
                if osc_dynamic_limits:
                    osc_range_limits = \
                        (0, 
                         min(abs(centred_point.phi - osc_dynamic_limits[0]),
                             abs(osc_dynamic_limits[1] - centred_point.phi)) /\
                         float(grid_properties["num_images_per_line"]))

                    self._acq_widget.update_osc_range_limits(osc_range_limits)
                    self._acq_widget.update_num_images_limits(\
                         grid_properties["num_lines"] * \
                         grid_properties["num_images_per_line"])
                    self._acq_widget.acq_widget_layout.osc_total_range_ledit.setText(str(\
                         grid_properties["num_images_per_line"] * \
                         float(self._acq_widget.acq_widget_layout.osc_range_ledit.text())))
                """

                grid.setSelected(True) 
                self.enable_grid_controls(True)
            else:
                grid.setSelected(False)

    def get_selected_grid(self):
        """Returns selected grids
        
        :returns: selected grid objects
        """
        for grid, grid_treewidget_item in self._grid_map.iteritems():
            if grid_treewidget_item.isSelected():
                return grid

    def get_selected_grid_properties(self):
        """Returns properties of the selected grid

        :returns: dict with properties
        """

        for grid, grid_treewidget_item in self._grid_map.iteritems():
            if grid_treewidget_item.isSelected():
                return grid.get_properties()

    def draw_grid_button_clicked(self):
        """Starts grid drawing
        """
        self._graphics_manager_hwobj.create_grid(self.spacing)

    def remove_grid_button_clicked(self):
        """Removes selected grid
        """
        grid_to_delete = self.get_selected_grid()

        if grid_to_delete:
            self._graphics_manager_hwobj.delete_shape(grid_to_delete)
            self._advanced_methods_widget.move_to_grid_button.setEnabled(False)           

    def hor_spacing_changed(self, value):
        """Updates spacing of the selected grid
        """
        try:
            self.spacing[0] = float(self._advanced_methods_widget.hor_spacing_ledit.text()) / 1000
            self.set_spacing()
        except:
            pass

    def ver_spacing_changed(self, value):
        """Updates spacing of the selected grid
        """
        try:
            self.spacing[1] = float(self._advanced_methods_widget.ver_spacing_ledit.text()) / 1000
            self.set_spacing()
        except:
            pass

    def set_spacing(self):
        if 0 in self.spacing:
            return

        for grid, treewidget_item in self._grid_map.iteritems():
            if treewidget_item.isSelected():
                grid.set_spacing(self.spacing, adjust_size=\
                   self._advanced_methods_widget.adjust_size_cbox.isChecked())
                grid_properties = grid.get_properties()

                
                treewidget_item.setText(1, str(grid_properties["num_lines"]))
                treewidget_item.setText(2, str(grid_properties["num_images_per_line"]))
                cell_count = grid_properties["num_lines"] * \
                             grid_properties["num_images_per_line"]
                self._acq_widget.acq_widget_layout.num_images_ledit.setText(\
                     str(grid_properties["num_lines"] * \
                         grid_properties["num_images_per_line"]))

    def move_to_grid(self):
        """Moves diffractometer to the center of the grid
        """
        grid = self.get_selected_grid()

        if grid:
            self._beamline_setup_hwobj.diffractometer_hwobj.\
                move_to_centred_position(grid.get_centred_position())

    def overlay_toggled(self, state):
        """Toggles (on/off) overlay
        """
        grid = self.get_selected_grid()

        if grid:
            grid.set_display_overlay(state)
           
    def overlay_alpha_changed(self, alpha_value):
        """Changes the transperency of the grid
        """
        grid = self.get_selected_grid()

        if grid:
            grid.set_fill_alpha(alpha_value)

    def overlay_change_color(self):
        """Changes the default color (blue) of overlay
        """
        color = QColorDialog.getColor()
        grid = self.get_selected_grid()

        if color.isValid() and grid:
            grid.set_base_color(color)

    def move_grid(self, direction):
        """Moves grid by one pix in selected direction

        :param direction: direction to move (right, left, up, down)
        :type direction: str
        """
        grid = self.get_selected_grid()

        if grid:
            grid.move_by_pix(direction)
            self._graphics_manager_hwobj.\
                 update_grid_motor_positions(grid)

    def enable_grid_controls(self, state):
        """Enables grid controls if a grid is selectd
        """
        self._advanced_methods_widget.overlay_cbox.setEnabled(state)
        self._advanced_methods_widget.overlay_slider.setEnabled(state)
        self._advanced_methods_widget.overlay_color_button.setEnabled(state)
        self._advanced_methods_widget.move_to_grid_button.setEnabled(state)
        self._advanced_methods_widget.remove_grid_button.setEnabled(state)        

        self._advanced_methods_widget.move_right_button.setEnabled(state)
        self._advanced_methods_widget.move_left_button.setEnabled(state)
        self._advanced_methods_widget.move_up_button.setEnabled(state)
        self._advanced_methods_widget.move_down_button.setEnabled(state)

        self._acq_widget.acq_widget_layout.\
             set_max_osc_range_button.setEnabled(state)

    def grid_osc_range_ledit_changed(self, new_value):
        """Osc range per frame changed

        :param new_value: new value
        :type new_value: str
        """
        
        self.update_grid_osc_total_range() 

    def grid_osc_total_range_ledit_changed(self, new_value):
        """Updates osc range per frame


        :param new_value: new value
        :type new_value: str
        """

        grid_properties = self.get_selected_grid_properties()
        if grid_properties:
            try:
                self._acq_widget.acq_widget_layout.osc_range_ledit.setText(\
                     "%.4f" % (float(new_value) / grid_properties["num_images_per_line"]))
            except:
                pass

    def update_grid_osc_total_range(self):
        """Updates osc range per line
        """

        grid_properties = self.get_selected_grid_properties()
        if grid_properties:
            self._acq_widget.acq_widget_layout.osc_total_range_ledit.setText(str(\
                float(self._acq_widget.acq_widget_layout.osc_range_ledit.text()) * \
                grid_properties["num_images_per_line"]))

    def set_max_osc_total_range_clicked(self, state):
        """Sets the osc range based on grid (number of images per line
           and osc in the middle of the grid)        
        """
        grid_properties = self.get_selected_grid_properties()
        if grid_properties:
            exposure_time = float(self._acq_widget.acq_widget_layout.exp_time_ledit.text())
            (lower, upper), result_exp_time = self._acq_widget.update_osc_total_range_limits(\
                 calc_by_speed=False,
                 num_images=grid_properties["num_images_per_line"],
                 exp_time=exposure_time)
            self._acq_widget.acq_widget_layout.osc_start_ledit.setText(\
                 "%.4f" % ((lower + upper) / 2))
            self._acq_widget.acq_widget_layout.osc_total_range_ledit.setText(\
                 "%.4f" % (abs(upper - lower)))
            self._acq_widget.acq_widget_layout.osc_range_ledit.setText(\
                 "%.4f" % (abs(lower - upper) / grid_properties["num_images_per_line"]))
            self._acq_widget.acq_widget_layout.exp_time_ledit.setText(\
                 "%.5f" % (result_exp_time))
