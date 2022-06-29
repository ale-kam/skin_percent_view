from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import Qt
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
from maya import cmds
import re


def mmw():
    main_window_ptr = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)
        

class SkinWin(QtWidgets.QDialog):
    
    @staticmethod
    def get_skin_cluster(mesh=None):
    # Get skin cluster from selected geo (split in case selection is subselect based)
        if not mesh:
            mesh = cmds.ls(sl=1, l=1)[0].split('.')[0]
        
        mesh_shape = cmds.listRelatives(mesh, shapes=1, f=1)[0]
        skn = [i for i in cmds.listHistory(mesh_shape) if cmds.nodeType(i) == 'skinCluster']
        if skn:
            return skn[0]
        else:
            return []
    
    
    def __init__(self, p=mmw()):
        super().__init__(p)
        self.setWindowTitle('Vert Skin Info')
        self.create_widgets()
        self.create_layouts()
        self.setMinimumSize(300, 100)

        
    def create_widgets(self):
        self.vert_label = QtWidgets.QLabel('None selected')
        self.vert_label.setStyleSheet("font-weight: bold")
        self.vert_label.setFont(QtGui.QFont('helvetica', 10))
        self.inf_list = QtWidgets.QListWidget()
        self.inf_list.setAlternatingRowColors(True)
        
        self.load_btn = QtWidgets.QPushButton("Load Vert")
        self.load_btn.clicked.connect(self.load_vert)
        
        self.refresh_btn = QtWidgets.QPushButton("Refresh Vert")
        self.refresh_btn.clicked.connect(self.refresh_vert)
        
    
        
    def create_layouts(self):
        self.main_col = QtWidgets.QVBoxLayout(self)
        self.main_col.addWidget(self.vert_label)
        self.main_col.addWidget(self.inf_list)
        
        self.btn_row = QtWidgets.QHBoxLayout()
        self.main_col.addLayout(self.btn_row)
        self.btn_row.addWidget(self.load_btn)
        self.btn_row.addWidget(self.refresh_btn)
        
    def add_vert_item(self, name, value):
        new_item = QtWidgets.QListWidgetItem()
        new_item.setSizeHint(QtCore.QSize(36, 36))
        self.inf_list.addItem(new_item)
        self.inf_list.setItemWidget(new_item, VertInfoItem(name, value))
        new_item.setFlags(Qt.NoItemFlags)
        
    def refresh_vert(self):
        vert = self.vert_label.text()
        if vert == 'None selected' or not cmds.objExists(vert):
            return
        self.vert_attached_inf(vert)
        
    def load_vert(self):
        selected_vert = [i for i in cmds.ls(sl=1, fl=1) if '.vtx[' in i]
        if not selected_vert:
            return
        selected_vert = selected_vert[-1]
        self.vert_attached_inf(selected_vert)
        
    
    def vert_attached_inf(self, vert):
        
        skn = SkinWin.get_skin_cluster(vert.split('.')[0])
        if not skn:
            cmds.warning("No skin cluster found on selected object")
            return

        infs = cmds.skinPercent(skn, vert, q=1, ignoreBelow=0.0001, t=None)
        inf_weights = [cmds.skinPercent(skn, t=i, q=1, v=1) for i in infs]
        results = list(zip(infs, inf_weights))
        results.sort(key=lambda x:x[1], reverse=True)
        self.inf_list.clear()
        for item in results:
            self.add_vert_item(item[0], item[1])
            
        self.vert_label.setText(vert)
        

        
class VertInfoItem(QtWidgets.QWidget):
    
    def __init__(self, name, value):
        super().__init__()
        self.main_row = QtWidgets.QHBoxLayout()
        self.main_row.addLayout(self.button_row())
        self.setLayout(self.main_row)
        
        font = QtGui.QFont('helvetica', 11)
        self.name = name
        self.value = value
        

        self.jnt_name = QtWidgets.QLabel(name)
        self.jnt_name.setFont(font)
        self.main_row.addWidget(self.jnt_name)
        
        self.weight_value = QtWidgets.QLabel('{0:.2f}'.format(value))
        self.weight_value.setFont(font)
        self.weight_value.setAlignment(Qt.AlignRight)
        self.main_row.addWidget(self.weight_value)
        
        self.setFixedHeight(36)
        
        
    def select_inf(self):
        inf = self.name
        if cmds.objExists(inf):
            cmds.select(inf, r=1)
        
    def button_row(self):
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(3)
        btn_icons = [':/ghostingObjectTypeJoint.png', ":/uvIsolateSelect.png", ":/uvIsolateSelectReset.png"]

        btn_methods = [self.select_inf,
                       lambda:self.select_skin_verts(True),
                       self.select_skin_verts]


        for i in range(3):
            btn = QtWidgets.QPushButton()
            btn.setFixedSize(16, 16)
            btn_layout.addWidget(btn)
            btn.setIcon(QtGui.QIcon(btn_icons[i]))
            btn.clicked.connect(btn_methods[i])
            
        return btn_layout
        

        
    def select_skin_verts(self, use_sel=False):
        
        jnt = self.name
        if use_sel:
            if not cmds.ls(sl=1):
                return
            skin = SkinWin.get_skin_cluster()
            
            if not skin:
                cmds.warning("No skin cluster found on selected mesh")
                return
            elif self.name not in cmds.skinCluster(skin, q=1, inf=1):
                cmds.warning("Influence not part of selected mesh's skin cluster")
                return
            else:
                skins = [skin]
            
        else:    
            skins = set([i for i in (cmds.listConnections(jnt) or []) if cmds.nodeType(i) == 'skinCluster'])
            
        
        sel_verts = []
        cmds.select(cl=1)
        for skin in skins:
            cmds.skinCluster(skin, e=1, siv=jnt)
            sel_verts.extend([i for i in cmds.ls(sl=1, fl=1) if '.vtx[' in i])
            
        cmds.select(sel_verts, r=1)
        

try:
    skin_win.deleteLater()
except:
    pass
    
skin_win = SkinWin()
skin_win.show()
        
    
    