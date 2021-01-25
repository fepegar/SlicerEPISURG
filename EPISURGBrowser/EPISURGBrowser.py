from pathlib import Path
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import ScriptedLoadableModule, ScriptedLoadableModuleWidget
from slicer.util import VTKObservationMixin

from EPISURGBase import EPISURGBaseLogic  # pylint: disable=import-error


class EPISURGBrowser(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    super().__init__(parent)
    self.parent.title = "EPISURG Browser"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["EPISURG"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#EPISURGBrowser">module documentation</a>.
"""
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""


class EPISURGBrowserWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self.subjects = None

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    self.logic = EPISURGBrowserLogic()
    self.makeGUI()
    slicer.episurgBrowser = self
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)

  def makeGUI(self):
    self.setDirButton = ctk.ctkCollapsibleButton()
    self.setDirButton.text = 'Select dataset directory'
    setDirLayout = qt.QFormLayout(self.setDirButton)
    self.layout.addWidget(self.setDirButton)

    self.datasetDirEdit = ctk.ctkPathLineEdit()
    self.datasetDirEdit.filters = ctk.ctkPathLineEdit.Dirs
    setDirLayout.addRow('EPISURG directory: ', self.datasetDirEdit)

    self.datasetDirButton = qt.QPushButton('Load subjects')
    self.datasetDirButton.clicked.connect(self.onLoadSubjectsButton)
    setDirLayout.addWidget(self.datasetDirButton)

    self.subjectsButton = ctk.ctkCollapsibleButton()
    self.subjectsButton.text = 'Select subject to load'
    self.subjectsButton.setEnabled(False)
    subjectsLayout = qt.QFormLayout(self.subjectsButton)
    self.layout.addWidget(self.subjectsButton)

    self.subjectsComboBox = qt.QComboBox()
    self.subjectsComboBox.addItem('Select subject ID')
    self.subjectsComboBox.currentIndexChanged.connect(self.onSubjectsComboBox)
    subjectsLayout.addWidget(self.subjectsComboBox)

    self.previousSubjectPushButton = qt.QPushButton('Previous')
    self.previousSubjectPushButton.clicked.connect(self.onPreviousSubjectButton)
    subjectsLayout.addWidget(self.previousSubjectPushButton)

    self.nextSubjectPushButton = qt.QPushButton('Next')
    self.nextSubjectPushButton.clicked.connect(self.onNextSubjectButton)
    subjectsLayout.addWidget(self.nextSubjectPushButton)

    self.layout.addStretch()

  def getSubjectsDict(self):
    datasetDir = Path(self.datasetDirEdit.currentPath).expanduser().absolute()
    if not datasetDir.is_dir():
      slicer.util.errorDisplay(f'{datasetDir} is not a directory')
      raise
    subjectsDir = datasetDir / 'subjects'
    if not subjectsDir.is_dir():
      slicer.util.errorDisplay(f'"subjects" directory not found in EPISURG directory "{datasetDir}"')
      raise
    pattern = 'sub-*'
    subjectsDirs = sorted(list(subjectsDir.glob(pattern)))
    if not subjectsDirs:
      slicer.util.errorDisplay(f'No directories found in {subjectsDir} with pattern {pattern}')
      raise
    subjectsDict = {
      d.name: Subject(d)
      for d in subjectsDirs
    }
    return subjectsDict

  def cleanupSubjects(self):
    for subject in self.subjects.values():
      subject.cleanup()

  def cleanup(self):
    """Called when the application closes and the module widget is destroyed."""
    self.removeObservers()

  # Slots
  def onLoadSubjectsButton(self):
    self.datasetDirEdit.addCurrentPathToHistory()
    self.subjects = self.getSubjectsDict()
    self.subjectsComboBox.blockSignals(True)
    self.subjectsComboBox.addItems(list(self.subjects.keys()))
    self.subjectsComboBox.setCurrentIndex(0)
    self.subjectsComboBox.blockSignals(False)
    self.setDirButton.setEnabled(False)
    self.subjectsButton.setEnabled(True)

  def onSceneStartClose(self, caller, event):
    """Called just before the scene is closed."""
    self.cleanupSubjects()

  def onPreviousSubjectButton(self):
    self.subjectsComboBox.currentIndex -= 1

  def onNextSubjectButton(self):
    self.subjectsComboBox.currentIndex += 1

  def onSubjectsComboBox(self):
    try:
      subject = self.subjects[self.subjectsComboBox.currentText]
    except KeyError:
      return

    try:
      self.cleanupSubjects()
      self.logic.closeScene()
      subject.load()
      self.logic.jumpToFirstSegment(subject.rater1SegNode)
    except Exception as e:
      slicer.util.errorDisplay(f'Failed to load subject: {e}')
      import traceback
      traceback.print_exc()


class EPISURGBrowserLogic(EPISURGBaseLogic):
  def __init__(self):
    super().__init__()


class Subject:

  RED = 222, 53, 7
  GREEN = 116, 191, 23
  BLUE = 24, 80, 201

  def __init__(self, subjectDir):
    self.dir = Path(subjectDir)
    self.id = self.dir.name
    self.t1PrePath = self.dir / 'preop' / f'{self.id}_preop-t1mri-1.nii.gz'
    self.t1PostDir = self.dir / 'postop'
    self.t1PostPath = self.t1PostDir / f'{self.id}_postop-t1mri-1.nii.gz'
    self.rater1SegPath = self.t1PostDir / f'{self.id}_postop-seg-1.nii.gz'
    self.rater2SegPath = self.t1PostDir / f'{self.id}_postop-seg-2.nii.gz'
    self.rater3SegPath = self.t1PostDir / f'{self.id}_postop-seg-3.nii.gz'
    self.cleanup()

  def __repr__(self):
    return f'Subject("{self.id}")'

  def cleanup(self):
    self.t1PreNode = None
    self.t1PostNode = None
    self.rater1SegNode = None
    self.rater2SegNode = None
    self.rater3SegNode = None

  def loadVolumeIfPresent(self, path):
    if not path.is_file(): return
    return slicer.util.loadVolume(str(path))

  def loadSegmentationIfPresent(self, path):
    if not path.is_file(): return
    segmentationNode = slicer.util.loadSegmentation(str(path))
    segmentation = segmentationNode.GetSegmentation()
    rule = slicer.vtkBinaryLabelmapToClosedSurfaceConversionRule
    segmentation.SetConversionParameter(rule.GetSmoothingFactorParameterName(), "0.2")
    segmentationNode.CreateClosedSurfaceRepresentation()
    displayNode = segmentationNode.GetDisplayNode()
    displayNode.SetVisibility2DFill(False)
    displayNode.SetAllSegmentsVisibility(True)
    displayNode.SetOpacity(0.75)
    return segmentationNode

  def load(self):
    self.t1PreNode = self.loadVolumeIfPresent(self.t1PrePath)
    self.t1PostNode = self.loadVolumeIfPresent(self.t1PostPath)
    self.rater1SegNode = self.loadSegmentationIfPresent(self.rater1SegPath)
    self.rater2SegNode = self.loadSegmentationIfPresent(self.rater2SegPath)
    self.rater3SegNode = self.loadSegmentationIfPresent(self.rater3SegPath)
    self.show()

  def show(self):
    slicer.util.setSliceViewerLayers(background=self.t1PostNode, foreground=self.t1PreNode)
    self.showSegment(self.rater1SegNode, self.GREEN)
    self.showSegment(self.rater2SegNode, self.BLUE)
    self.showSegment(self.rater3SegNode, self.RED)

  def showSegment(self, segmentationNode, color):
    if segmentationNode is None: return
    color = [c / 255 for c in color]
    segment = segmentationNode.GetSegmentation().GetSegment('Segment_1')
    segment.SetName('Resection cavity')
    segment.SetColor(color)
