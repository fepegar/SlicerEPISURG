from pathlib import Path
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import ScriptedLoadableModule, ScriptedLoadableModuleLogic
from slicer.util import VTKObservationMixin


class EPISURGBase(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "EPISURG Base"
    self.parent.categories = ["EPISURG"]
    self.parent.dependencies = []
    self.parent.contributors = ["Fernando Perez-Garcia (University College London & King's College London"]
    self.parent.helpText = ''
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = ''


class EPISURGBaseLogic(ScriptedLoadableModuleLogic):
  def __init__(self):
    super().__init__()

  def getSegmentsNames(self, segmentationNode):
    array = vtk.vtkStringArray()
    segmentationNode.GetSegmentation().GetSegmentIDs(array)
    names = [array.GetValue(i) for i in range(array.GetNumberOfValues())]
    return names

  def jumpToFirstSegment(self, segmentationNode):
    if segmentationNode is None: return
    name = self.getSegmentsNames(segmentationNode)[0]
    center = segmentationNode.GetSegmentCenterRAS(name)
    if center is None:
      slicer.util.errorDisplay('')
    colors = 'Yellow', 'Green', 'Red'
    for (color, offset) in zip(colors, center):
      sliceLogic = slicer.app.layoutManager().sliceWidget(color).sliceLogic()
      sliceLogic.SetSliceOffset(offset)
    layoutManager = slicer.app.layoutManager()
    threeDWidget = layoutManager.threeDWidget(0)
    threeDView = threeDWidget.threeDView()
    threeDView.setFocalPoint(*center)

  def closeScene(self, code=0):
    slicer.mrmlScene.Clear(code)
