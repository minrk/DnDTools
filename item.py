#!/usr/bin/env python
import sys
from os.path import isfile
from subprocess import Popen
from xml.etree import ElementTree as ET
lorem="Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."

slots="Head Neck Waist MainHand OffHand Body Arm Hand Ring Feet Symbol/Ki Tattoo".split()
def escape(multiline):
    return multiline.replace("\n","<br/>")
def tonicerstring(root,tags=None,html=False):
    if tags is None:
        return ET.tostring(root).replace("><",">\n<")
    else:
        s = ET.tostring(root)
        if html:
            s = escape(s)
        for tag in tags:
            s = s.replace("</%s>"%tag, "</%s>\n"%tag)
        return s

def text(s):
    if s is None:
        return " "
    else:
        return str(s) or " "

def HTMLCard(it):
    isweapon=isinstance(it, Weapon)
    isarmor = isinstance(it, Armor)
    card = ET.Element("div", id="card")
    
    # header
    header = ET.SubElement(card, "div", id="cardheader", Class=it.itemtype.lower())
    if not isweapon:
        ET.SubElement(header, "div", id="slot", Class="littlebox").text=text(it.slot)
    else:
        ET.SubElement(header, "div", id="slot", Class="littlebox").text=text(it.group)
    ET.SubElement(header, "div", id="name").text=text(it.name)
    if isweapon: # insert Weapon Group
        pass
        # ET.SubElement(header, "div", id="weapongroup", Class="littlebox").text=text(it.slot)
    ET.SubElement(header, "div", id="description").text=text(it.description)
    if it.keywords:
        ET.SubElement(card, "div", id="keywords").text="Keywords: "+", ".join(it.keywords)
    
    # card body
    body = ET.SubElement(card, "div", id="cardbody")
    
    if isarmor: # add Armor Table
        armordiv=ET.SubElement(body, "div", id="armordiv", Class="subclass")
        armortable=ET.SubElement(armordiv, "table", Class="armortable")
        hrow = ET.SubElement(armortable, "tr", Class="head")
        for s in "AC Enhancement Check Speed".split():
            ET.SubElement(hrow, "td").text=s
        hrow = ET.SubElement(armortable, "tr")
        for s in (it.ACBonus, it.enhancement, it.armorCheck, it.speedCheck):
            ET.SubElement(hrow, "td").text=text(s)
    
    if isweapon: # add Weapon Table
        weapondiv=ET.SubElement(body, "div", id="weapondiv", Class="subclass")
        weapontable=ET.SubElement(weapondiv, "table", Class="weapontable")
        hrow = ET.SubElement(weapontable, "tr", Class="head")
        for s in "Hand Type Prof Damage Range".split():
            ET.SubElement(hrow, "td").text=s
        hrow = ET.SubElement(weapontable, "tr")
        for s in (it.slot, it.weapontype, it.proficiency, it.dice, it.range):
            ET.SubElement(hrow, "td").text=text(s)
        if it.properties:
            weaponprops=ET.SubElement(weapondiv, "div", id="properties")
            ul=ET.SubElement(weaponprops, "ul")
            ul.text="  "
            for p in it.properties:
                definition = Weapon.Properties.get(p, "")
                if definition:
                    txt = "%s: %s"%(p, definition)
                else:
                    txt = text(p)
                ET.SubElement(ul, "li").text=txt
    
    # features
    # if it.features:
    features = ET.SubElement(body, "div", id="features")
    ul=ET.SubElement(features, "ul")
    ul.text=" "
    for feat in it.features:
        ET.SubElement(ul, "li").text=text(feat)
    
    # bottom row
    ET.SubElement(card, "div", id="flavor").text=text(it.flavor)
    value=it.value
    if value and value[-1] in '1234567890':
        value = value+'gp'
    ET.SubElement(card, "div", id="value", Class="littlebox").text=text(value)
    # ET.SubElement(card, "div", id="level", Class="littlebox").text="Lvl "+it.level
    # print tonicerstring(card)
    return card
    

def HTMLCardList(itemlist):
    pages = []
    for n,it in enumerate(itemlist):
        if n%9 == 0:
            pagetable = ET.Element("table",cellpadding="0",cellspacing="1px")
            pages.append(pagetable)
        if n%3 == 0:
            row = ET.SubElement(pagetable, "tr")
        ET.SubElement(row, "td").append(HTMLCard(it))
    
    for page in pages:
        pass
        # print tonicerstring(page, tags=("tr", "table","li"))
    return pages

        

class Item(object):
    """docstring for Item"""
    itemtype="Item"
    def __init__(self, name):
        super(Item, self).__init__()
        if not isinstance(name, (str,unicode)):
            self.load(name)
        else:
            self.name = name
            self.slot="MainHand"
            self.value="0gp"
            self.description=lorem
            self.flavor=lorem
            self.features=[]
            self.keywords=[]
            self.level="1"
            self.etree = None
    
    def render(self):
        self.root = ET.Element(self.itemtype)
        # ET.SubElement(self.root, "itemtype").text=self.itemtype
        for entry in ["level", "name","slot","value","description","flavor"]:
            value = getattr(self, entry)
            if value is None:
                value = ""
            ET.SubElement(self.root, entry).text=str(value)
        # self.render_features(self.root)
        for key in self.keywords:
            ET.SubElement(self.root, "keyword").text=key
        for feature in self.features:
            ET.SubElement(self.root, "feature").text=str(feature)
        
        return ET.ElementTree(self.root)
    
    def __repr__(self):
        if len(self.name) > 24:
            shortname = self.name[:21]+"..."
        else:
            shortname=self.name
        return "Lvl %s %s: '%s' %s %s"%(self.level,self.itemtype, shortname, self.slot, self._subrepr())
    
    _subrepr=lambda self: ""
    
    def __str__(self):
        etree = self.render()
        start = ET.tostring(etree.getroot())
        return start.replace("><",">\n    <").replace("    </%s>"%self.itemtype,"</%s>"%self.itemtype)
    
    def __eq__(self,other):
        for atr in "level name slot value description flavor".split():
            if getattr(self,atr) != getattr(other,atr):
                # print "%s %s != %s"%(atr, getattr(self,atr),getattr(other,atr))
                return False
        for atr in "keywords features".split():
            if set(getattr(self,atr)) != set(getattr(other,atr)):
                # print atr, set(getattr(self,atr)), "!=", set(getattr(other,atr))
                return False
        return True
    
    def save(self, fname,mode='a'):
        assert mode == 'a' or mode == 'w', "must open in a write mode!"
        fp = open(fname, mode)
        fp.write(str(self))
        fp.close()
    
    def load(self, etree):
        if isinstance(etree, ET.ElementTree):
            self.root = etree.getroot()
        else: # assume we got root
            self.root = etree
        assert self.root.tag.lower() == self.itemtype.lower(), "wrong type"
        for key in "name level slot value description flavor".split():
            setattr(self, key, getattr(self.root.find(key),"text",""))
        
        self.keywords = []
        for keyword in self.root.findall("keyword"):
            self.keywords.append(keyword.text)
        self.features = []
        for feat in self.root.findall("feature"):
            self.features.append(feat.text)
    
    def isin(self, iter):
        for it in iter:
            if self == it:
                return True
        return False
    

_weapontypes=[]
for mod in "Simple Military Superior Improvised".split():
    for kind in "Melee Ranged".split():
        _weapontypes.append("%s %s"%(mod,kind))
    
class Weapon(Item):
    """docstring for Weapon"""
    itemtype="Weapon"
    Groups="Unarmed Axe Bow Crossbow Flail Hammer HeavyBlade LightBlade Mace Pick Polearm Sling Spear Staff".split()
    Properties=dict(HeavyThrown="use STR",
                            HighCrit="extra 1[W] crit damage (+1[W] each tier)",
                            LightThrown="use DEX",
                            OffHand="",
                            Reach="attack=close burst 2, no threat bonus",
                            Small="",
                            Versatile="1 or 2-handed (+1 dmg if 2)",
                            LoadFree="Load as free action",
                            LoadMinor="Load as minor action")
    
    types=_weapontypes
    def __init__(self, name):
        self.proficiency="+1"
        self.dice="1d4"
        self.range="-"
        self.group=self.Groups[0]
        self.weapontype=self.types[0]
        self.properties=[]
        super(Weapon, self).__init__(name)
    
    def load(self, etree):
        Item.load(self, etree)
        for key in "group proficiency dice range".split():
            setattr(self, key, getattr(self.root.find(key),"text",""))
        
        self.properties = []
        for prop in self.root.findall("property"):
            self.properties.append(prop.text)
    
    def __eq__(self,other):
        if not Item.__eq__(self, other):
            return False
        for atr in "group proficiency dice range".split():
            if getattr(self,atr) != getattr(other,atr):
                # print "a.%s %s != %s"%(atr, getattr(self,atr),getattr(other,atr))
                return False
        for atr in "properties".split():
            if set(getattr(self,atr)) != set(getattr(other,atr)):
                # print atr, set(getattr(self,atr)), "!=", set(getattr(other,atr))
                return False
        return True
    
    def _subrepr(self):
        return "%s %s %s"%(self.weapontype, self.proficiency, self.group)
    
    def render(self):
        etree = Item.render(self)
        root = etree.getroot()
        for key in "group proficiency dice range weapontype".split():
            value = getattr(self, key)
            ET.SubElement(self.root, key).text=str(value)
        for p in self.properties:
            ET.SubElement(root, "property").text=p
        return etree
    

class Armor(Item):
    """docstring for Armor"""
    itemtype="Armor"
    types="Cloth Leather Hide Chain Scale Plate LightShield HeavyShield".split()
    def __init__(self, name):
        self.ACBonus="+1"
        self.enhancement="-"
        self.armorCheck="-"
        self.speedCheck="-"
        self.slot=self.types[0]
        super(Armor, self).__init__(name)
    
    def load(self, etree):
        Item.load(self, etree)
        for key in "ACBonus enhancement armorCheck speedCheck".split():
            # print key, getattr(self.root.find(key),"text","")
            setattr(self, key, getattr(self.root.find(key),"text",""))
            # print getattr(self, key)
    
    def __eq__(self,other):
        if not Item.__eq__(self, other):
            return False
        for atr in "ACBonus enhancement armorCheck speedCheck".split():
            if getattr(self,atr) != getattr(other,atr):
                # print "a.%s %s != %s"%(atr, getattr(self,atr),getattr(other,atr))
                return False
        return True
    
    def _subrepr(self):
        return "%s AC, %s, %s"%(self.ACBonus, self.armorCheck, self.speedCheck)
    
    def render(self):
        etree = Item.render(self)
        root = etree.getroot()
        for key in "ACBonus enhancement armorCheck speedCheck".split():
            value = getattr(self, key)
            if value is None:
                value = "-"
            ET.SubElement(self.root, key).text=str(value)
        return etree
    


def loadItem(s):
    # print s
    if isinstance(s,str):
        etree = ET.parse(s)
    else:
        etree = ET.ElementTree(s)
    root = etree.getroot()
    # print root
    # print ET.tostring(root)
    # print root.tag.lower()
    if root.tag.lower() == "item":
        return Item(root)
    elif root.tag.lower() == "weapon":
        return Weapon(root)
    elif root.tag.lower() == "armor":
        return Armor(root)

def loadItemList(fname):
    etree = ET.parse(fname)
    root = etree.getroot()
    # print root
    if root.tag.lower() == "itemlist":
        return map(loadItem, root.getchildren())
    else:
        return [loadItem(root)]

def writeItemList(itemlist, fname,mode='w'):
    if mode == 'a' and isfile(fname):
        olditems=loadItemList(fname)
    else:
        olditems=[]
    fp = open(fname, 'w')
    fp.write("<itemlist>\n")
    for it in olditems:
        fp.write(str(it)+'\n')
    for it in itemlist:
        fp.write(str(it)+'\n')
    fp.write("</itemlist>\n")
    fp.close()

def writeHTMLItemTables(itemlist, fname,separate=False,embedStyle=False,openAfter=True):
    if separate:
        for i in range((len(itemlist)-1)/9+1):
            writeHTMLItemTables(("page%i."%i)+fname)
        return
    pages = HTMLCardList(itemlist)
    fp = open(fname, 'w')
    if embedStyle:
        sfp = open("style.css")
        style="<style>%s</style>"%sfp.read()
        sfp.close()
    else:
        style="""<link rel="stylesheet" href="style.css" type="text/css" />"""
    fp.write("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
    
<head>
	<meta http-equiv="content-type" content="text/html; charset=utf-8" />
	<title>
		D&amp;D Items
	</title>
    %s
</head>
<body> 	
"""%style)
    for page in pages:
        fp.write(tonicerstring(page, tags=("tr", "table","li","div"),html=True)+\
        "<div id=pagebreak></div>")
    fp.write("""</body></html>""")
    fp.close()
    if sys.platform == "darwin":
        Popen(["open",fname])
    

