
from os.path import dirname,basename
import wx
from wx.lib.scrolledpanel import ScrolledPanel
# from item import Item, Armor,Weapon,slots
import item 
lorem="Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
MAX_SPECIALS=10
MAX_ITEMS=50
LINES=20
######### default flags
major = {'border':20, 'flag': wx.ALIGN_CENTER | wx.ALL|wx.EXPAND}
minor = {'border':4, 'flag': wx.ALIGN_CENTER | wx.ALL}
bulk = {'border':4, 'flag': wx.ALIGN_CENTER | wx.ALL|wx.EXPAND}

class DandDGUI(wx.Notebook):
    """the parent object for the washermark GUI system"""
    def __init__(self,parent=None,id=-1):
        wx.Notebook.__init__(self, parent, id)
        # build pages
        self.inv  = InventoryPanel(self)
        self.ip = ItemPanel(self)
        self.wp = WeaponPanel(self)
        self.ap  = ArmorPanel(self)
        self.AddPage(self.inv, "Inventory")
        self.AddPage(self.ip, "Item")
        self.AddPage(self.wp, "Weapon")
        self.AddPage(self.ap, "Armor")
        wx.CallAfter(self.OnLoad)
        # print self.this
    
    def OnLoad(self):
        """This is a test function, don't keep it"""
        return
        it = item.Item("Bigby's Thing")
        it.slot = item.slots[2]
        it.level="3"
        it.value="300gp"
        it.keywords="Radiant Fire Martial".split()
        it.description="Bigby had a thing and it was this thing"
        it.flavor="I HAS A FLAVR"
        it.features.append("I is a feature!")
        it.features.append("Power (Daily):\n    ANOTHER FEATURE")
        self.inv.addItem(it)
    
    def addItem(self, panel):
        name = panel.name.GetValue()
        print name
        if panel is self.ip:
            it = item.Item(name)
        elif panel is self.wp:
            it = item.Weapon(name)
        elif panel is self.ap:
            it = item.Armor(name)
        it.value = panel.value.GetValue()
        it.level=panel.level.GetStringSelection() or ""
        it.slot=panel.slot.GetStringSelection() or ""
        keywordstr = str(panel.keywords.GetValue()).strip()
        if keywordstr:
            it.keywords = map(str.strip, map(str, keywordstr.split(",")))
        it.description=panel.description.GetValue()
        it.flavor=panel.flavor.GetValue()
        nfeatures = panel.nfeatures
        it.features=[]
        for i in range(nfeatures):
            feat=panel.features[i].GetValue()
            if feat:
                it.features.append(feat)
        if panel is self.wp:
            for atr in "proficiency dice weapontype group".split():
                setattr(it, atr,getattr(panel,atr).GetStringSelection() or "")
            propstr = str(panel.properties.GetValue()).strip()
            if propstr:
                it.properties = map(str.strip, map(str, propstr.split(",")))
            if "Ranged" in it.weapontype:
                it.range = panel.range.GetValue()
        
        elif panel is self.ap:
            for atr in "ACBonus enhancement armorCheck speedCheck".split():
                setattr(it, atr,getattr(panel,atr).GetStringSelection() or "")
        self.inv.addItem(it)
        self.SetSelection(0)
    
    def activateItem(self, it):
        if isinstance(it, item.Weapon):
            self.wp.loadItem(it)
            self.SetSelection(2)
        elif isinstance(it, item.Armor):
            self.ap.loadItem(it)
            self.SetSelection(3)
        else:
            self.ip.loadItem(it)
            self.SetSelection(1)
    


class ItemPanel(ScrolledPanel):
    """The GUI"""
    levels=map(str, range(1,31))
    slots=item.slots
    buildSubclass=lambda self: None
    layoutSubclass=lambda self: None
    subclassFlags=bulk
    
    def __init__(self,parent,id=-1):
        self.nfeatures=0
        self.parent=parent
        super(ItemPanel, self).__init__(parent,id)
        self.SetupScrolling()
        self.buildForm()
        self.doLayout()
        # self.
        wx.CallAfter(self.OnLoad)
        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPage)
    
    def twiddle(self): # from http://www.velocityreviews.com/forums/t330788-how-to-update-window-after-wxgrid-is-updated.html 
        x,y = self.GetSize() 
        self.SetSize((x, y+1)) 
        self.SetSize((x,y))
    
    def loadItem(self, it):
        for atr in "name value description flavor".split():
            getattr(self, atr).SetValue(getattr(it, atr,""))
        
        for atr in "keywords".split():
            getattr(self, atr).SetValue(", ".join(getattr(it, atr, "")))
        for i in range(self.nfeatures):
            self.OnDropFeat(0)
        for feat in it.features:
            self.features[self.nfeatures].SetValue(feat)
            self.OnAddFeat(0)
        
        self.level.SetStringSelection(it.level)
        self.slot.SetStringSelection(it.slot)
            
            
        
    def buildForm(self):
        """builds the form"""
        self.name = wx.TextCtrl(self, size=(300,LINES))
        self.level=wx.Choice(self)
        self.level.AppendItems(strings=self.levels)
        self.slot=wx.Choice(self)
        self.slot.AppendItems(strings=self.slots)
        self.value = wx.TextCtrl(self, size=(50,LINES))
        
        # subclass part goes here
        self.buildSubclass()
        
        self.keywords = wx.TextCtrl(self, size=(400,LINES))
        self.description = wx.TextCtrl(self, size=(400,3*LINES),style=wx.TE_MULTILINE)
        self.flavor = wx.TextCtrl(self, size=(400,3*LINES), style=wx.TE_MULTILINE)
        self.features = [wx.TextCtrl(self, size=(400,2*LINES),style=wx.TE_MULTILINE) for i in range(MAX_SPECIALS)]
        for feat in self.features:
            feat.Hide()
        self.addFeature = wx.Button(self, label="Add Feature")
        self.addFeature.Bind(wx.EVT_BUTTON, self.OnAddFeat)
        self.dropFeature = wx.Button(self, label="Drop Feature")
        self.dropFeature.Bind(wx.EVT_BUTTON, self.OnDropFeat)
        self.generate = wx.Button(self, label="Save Item")
        self.generate.Bind(wx.EVT_BUTTON, self.OnGenerate)
    
    def OnLoad(self):
        return
        self.nfeatures=MAX_SPECIALS
        for i in range(MAX_SPECIALS):
            self.OnDropFeat(0)
    
    
    def doLayout(self):
        ''' Layout the controls by means of sizers. '''
        
        # Our Sizers
        boxSizer = wx.BoxSizer(orient=wx.VERTICAL)
        # outputBoxSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        
        # Add the controls to the sizers:
        # boxSizer.add()
        sizer=wx.BoxSizer(orient=wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label="Name:"),**minor)
        sizer.Add(self.name,**bulk)
        sizer.Add(wx.StaticText(self, label="Level:"),**minor)
        sizer.Add(self.level,**minor)
        sizer.Add(wx.StaticText(self, label="Slot:"),**minor)
        sizer.Add(self.slot,**minor)
        sizer.Add(wx.StaticText(self, label="Value:"),**minor)
        sizer.Add(self.value,**bulk)
        boxSizer.Add(sizer,**bulk)
        subsizer=self.layoutSubclass()
        if subsizer:
            boxSizer.Add(subsizer,**self.subclassFlags)
        sizer=wx.BoxSizer(orient=wx.HORIZONTAL)
        boxSizer.Add(wx.StaticText(self, label="Keywords (comma separated): i.e. Radiant, Fire, Martial"))
        boxSizer.Add(self.keywords,**bulk)
        boxSizer.Add(wx.StaticText(self, label="Description:"))
        boxSizer.Add(self.description,**bulk)
        boxSizer.Add(wx.StaticText(self, label="Flavor:"))
        boxSizer.Add(self.flavor,**bulk)
        boxSizer.Add(wx.StaticText(self, label="Features:"))
        # featureSizer=self.drawStats()
        sizer=wx.BoxSizer(orient=wx.HORIZONTAL)
        sizer.Add(self.addFeature,**minor)
        sizer.Add(self.dropFeature,**minor)
        sizer.Add(self.generate,**minor)
        boxSizer.Add(sizer,**bulk)
        # self.featureSizer=wx.BoxSizer(orient=wx.VERTICAL)
        for feature in self.features:
            boxSizer.Add(feature,**bulk)
        
        # boxSizer.Add(wx.StaticText(self, label="BitString:"), **minor)
        self.SetSizer(boxSizer)
        self.sizer=boxSizer    
    
    def OnGenerate(self, evt):
        self.parent.addItem(self)
    
    def OnPage(self, evt):
        for p in self.ip, self.wp, self.ap, self.inv:
            p.twiddle()
    
    def OnAddFeat(self,evt):
        if self.nfeatures < MAX_SPECIALS:
            self.features[self.nfeatures].Show()
            self.nfeatures += 1
        self.twiddle()
        self.Update()
    
    def OnDropFeat(self,evt):
        if self.nfeatures > 0:
            self.nfeatures -= 1
            self.features[self.nfeatures].Hide()
            self.features[self.nfeatures].SetValue("")
        self.twiddle()
        self.Update()
    


class WeaponPanel(ItemPanel):
    """docstring for WeaponPanel"""
    subclassFlags=bulk
    slots="MainHand OffHand TwoHand".split()
    proficiencies=["+%i"%i for i in range(1,10) ]
    dices=["%id%i"%(n,s) for n in range(1,4) for s in range(4,13,2)+[20] ]
    
    def loadItem(self,it):
        ItemPanel.loadItem(self, it)
        self.properties.SetValue(", ".join(getattr(it, "properties","")))
        for choice in "proficiency dice group weapontype".split():
            getattr(self, choice).SetStringSelection(getattr(it, choice,""))
    
    def buildSubclass(self):
        self.proficiency=wx.Choice(self)
        self.proficiency.SetItems(self.proficiencies)
        self.dice=wx.Choice(self)
        self.dice.SetItems(self.dices)
        self.group=wx.Choice(self)
        self.group.AppendItems(item.Weapon.Groups)
        self.weapontype=wx.Choice(self)
        self.weapontype.AppendItems(item.Weapon.types)
        self.weapontype.Bind(wx.EVT_CHOICE, self.OnType)
        self.range=wx.TextCtrl(self,size=(64,LINES))
        self.rangeLabel=wx.StaticText(self, label="Range")
        self.properties=wx.TextCtrl(self, size=(128,LINES))
    
    def layoutSubclass(self):
        fsizer = wx.FlexGridSizer(rows=2,cols=5,hgap=8)
        flag=wx.ALIGN_CENTER
        fsizer.AddMany([(wx.StaticText(self, label="Prof"),flag),
                        (wx.StaticText(self, label="Dice"),flag),
                        (wx.StaticText(self, label="Group"),flag),
                        (wx.StaticText(self, label="Class"),flag),
                        (self.rangeLabel,flag),
                        (self.proficiency,flag),(self.dice,flag),
                        (self.group,flag),(self.weapontype,flag),
                        (self.range,flag)]
        )
        sizer = wx.BoxSizer( wx.VERTICAL)
        sizer.Add(fsizer, **bulk)
        sizer.Add(wx.StaticText(self, label="Properties: HeavyThrown, Small, etc."))
        sizer.Add(self.properties,**bulk)
        return sizer
    
    def OnType(self, evt):
        if "Ranged" in self.weapontype.GetStringSelection():
            self.range.Show()
            self.rangeLabel.Show()
        else:
            self.range.Hide()
            self.rangeLabel.Hide()
    


class ArmorPanel(ItemPanel):
    """docstring for ArmorPanel"""
    subclassFlags=bulk
    
    
    def loadItem(self,it):
        ItemPanel.loadItem(self, it)
        for choice in "ACBonus enhancement armorCheck speedCheck".split():
            getattr(self, choice).SetStringSelection(getattr(it, choice,""))
    
    def buildSubclass(self):
        self.slot.SetItems(item.Armor.types)
        self.ACBonus=wx.Choice(self)
        for i in range(1,15):
            self.ACBonus.Append("+%i"%i)
        
        self.enhancement=wx.Choice(self)
        for i in range(0,19):
            self.enhancement.Append("+%i"%i)
        
        self.armorCheck=wx.Choice(self)
        self.armorCheck.AppendItems("- -1 -2 -3".split())
        
        self.speedCheck=wx.Choice(self)
        self.speedCheck.AppendItems("- -1 -2 -3".split())
    
    def layoutSubclass(self):
        sizer = wx.FlexGridSizer(rows=2,cols=4,hgap=8)
        flag=wx.ALIGN_CENTER
        sizer.AddMany([(wx.StaticText(self, label="AC"),flag),
                        (wx.StaticText(self, label="Enhancement"),flag),
                        (wx.StaticText(self, label="Check"),flag),
                        (wx.StaticText(self, label="Speed"),flag),
                        (self.ACBonus,flag),(self.enhancement,flag),
                        (self.armorCheck,flag),(self.speedCheck,flag)]
        )
        return sizer
    


class InventoryRow(object):
    def __init__(self, panel, index):
        self.index=index
        self.panel=panel
        self.sizer=wx.BoxSizer(wx.HORIZONTAL)
        self.copy=wx.Button(panel, label="Load")
        self.copy.Bind(wx.EVT_BUTTON, self.OnCopy)
        self.sizer.Add(self.copy,**bulk)
        self.delete=wx.Button(panel, label="Delete")
        self.delete.Bind(wx.EVT_BUTTON, self.OnDelete)
        self.sizer.Add(self.delete,**bulk)
        self.field=wx.TextCtrl(panel, size=(500,LINES),style=wx.TE_READONLY)
        self.sizer.Add(self.field,**bulk)
        self.hide()
    
    def hide(self):
        self.field.Hide()
        self.copy.Hide()
        self.delete.Hide()
    
    def show(self):
        self.field.Show()
        self.copy.Show()
        self.delete.Show()
    
    def OnCopy(self,evt):
        self.panel.parent.activateItem(self.panel.items[self.index])
    
    def OnDelete(self, evt):
        self.panel.dropItem(self.index)
    


class InventoryPanel(ScrolledPanel):
    """The Inventory"""
    def twiddle(self): # from http://www.velocityreviews.com/forums/t330788-how-to-update-window-after-wxgrid-is-updated.html 
        x,y = self.GetSize() 
        self.SetSize((x, y+1)) 
        self.SetSize((x,y)) 
    
    def __init__(self,parent,id=-1):
        self.items=[]
        self.rows=[]
        self.parent=parent
        # .__init__(self, parent, id)
        super(InventoryPanel, self).__init__(parent,id)
        self.SetupScrolling()
        self.buildForm()
        self.doLayout()
        self.activeFile=""
        self.activeDir=dirname(self.activeFile)
        # wx.CallAfter(self.OnLoad)
    
    def buildForm(self):
        """builds the form"""
        self.load=wx.Button(self, label="Load Items")
        self.load.Bind(wx.EVT_BUTTON, self.LoadItems)
        self.save=wx.Button(self, label="Save Items")
        self.save.Bind(wx.EVT_BUTTON, self.SaveItems)
        self.render=wx.Button(self, label="Render HTML Cards")
        self.render.Bind(wx.EVT_BUTTON, self.RenderHTML)
        for i in range(MAX_ITEMS):
            self.rows.append(InventoryRow(self, i))
    
    def doLayout(self):
        ''' Layout the controls by means of sizers. '''
        
        # Our Sizers
        boxSizer = wx.BoxSizer(orient=wx.VERTICAL)
        
        sizer=wx.BoxSizer(orient=wx.HORIZONTAL)
        sizer.Add(self.load, **bulk)
        sizer.Add(self.save, **bulk)
        sizer.Add(self.render, **bulk)
        boxSizer.Add(sizer)
        for row in self.rows:
            boxSizer.Add(row.sizer)
        self.SetSizer(boxSizer)
        self.sizer=boxSizer
    
    def addItem(self, it):
        if it.isin(self.items):
            return
        assert not len(self.items) >= MAX_ITEMS, "reached max %i items!"%(MAX_ITEMS)
        n = len(self.items)
        self.rows[n].field.SetValue(repr(it))
        self.rows[n].show()
        self.items.append(it)
        self.twiddle()
    
    def dropItem(self, index):
        n = len(self.items)
        for i in range(index, n):
            self.rows[i].field.SetValue(self.rows[i+1].field.GetValue())
        self.items.pop(index)
        # self.nitems -= 1
        self.rows[n-1].hide()
        self.twiddle()
    
    def LoadItems(self, evt):
        dlg = wx.FileDialog(self, message="Load ItemList from XML", defaultDir=self.activeDir,
                            defaultFile=basename(self.activeFile),
                            wildcard="*.XML|*.xml",style=wx.FD_OPEN)
        if dlg.ShowModal():
            path=dlg.GetPath()
            self.activeFile=path
            self.activeDir=dirname(path)
            itemlist = item.loadItemList(path)
            for it in itemlist:
                self.addItem(it)
        dlg.Destroy()
    
    def SaveItems(self, evt):
        dlg = wx.FileDialog(self, message="Save ItemList to XML", defaultDir=self.activeDir,
                            defaultFile=basename(self.activeFile), 
                            wildcard="*.XML|*.xml",style=wx.FD_SAVE)
        if dlg.ShowModal():
            path=dlg.GetPath()
            self.activeFile=path
            self.activeDir=dirname(path)
            item.writeItemList(self.items,path)
        dlg.Destroy()
    
    def RenderHTML(self, evt):
        dlg = wx.FileDialog(self, message="Render Items to HTML", defaultDir=self.activeDir,
                            defaultFile=basename(self.activeFile.replace("xml","html")), 
                            wildcard="*.HTML|*.html",style=wx.FD_SAVE)
        if dlg.ShowModal():
            path=dlg.GetPath()
            item.writeHTMLItemTables(self.items,path,embedStyle=True)
        dlg.Destroy()
    

if __name__ == '__main__':
    app=wx.PySimpleApp()

    f = wx.Frame(None, -1, size=(800,600), name="DandD Items")
    gui = DandDGUI(f)
    f.Show(1)
    app.MainLoop()
    
    
