"""
A database interface for examining the defenses and roles of D&D4e monsters.
It will use Safari on OSX to populate the database. If I bothered to figure out 
how to get cookies and sessions to work with D&DI, this would be unnecessary.

Standard usage model:

>>> e = connectDB("/path/to/mymonsters.db")
>>> M = MonsterDB(e)
>>> solos = M.solos
>>> group = M.get(Monster.level < 21, Monster.level >= 10, Monster.role != "Brute")
>>> for m in group:
         print m

etc.

"""


import re,os
from subprocess import Popen, PIPE
from string import printable

from xml.etree import ElementTree as etree
from urllib import urlretrieve,urlencode

# logged_in = True # hope
try:
    import pylab
    from pylab import *
    import numpy
    from numpy import *
except ImportError:
    pass

from sqlalchemy import *
from sqlalchemy import orm

metadata = MetaData()

root_url = "http://www.wizards.com/dndinsider/compendium/compendiumSearch.asmx"

def unescape(s):
    s = s.replace("\xe2\x80\x99","'")
    return "".join([ c for c in s if c in printable ])

class Monster(object):
    """An object to represent Monsters."""
    AC=fortitude=reflex=will=level=id=HP=0
    leader=False
    role=""
    group=""
    
    def __init__(self, name,id):
        self.name = unescape(name)
        self.id = id
    
    @property
    def defenses(self):
        return [self.AC, self.fortitude, self.reflex, self.will]
    
    @defenses.setter
    def defenses(self, value):
        self.AC, self.fortitude, self.reflex, self.will = value
    
    def load(self, *args):
        self.level, self.AC, self.fortitude, self.reflex, self.will = value
    
    def __str__(self):
        s = "%s"%(self.name)
        s += ":\n    "
        s += "Level %i %s %s"%(self.level, self.group, self.role)
        if self.leader:
            s += " (Leader)"
        s += "\n    "
        s += "HP: %i  AC: %i  Fort: %i  Ref: %i  Will: %i"%tuple([self.HP]+self.defenses)
        s += "\n    Compendium ID#%i"%self.id
        return s
    def __repr__(self):
        return "< %s: Level %i %s >"%(self.name, self.level, self.group or self.role)

# sorting keys
HP = lambda m: m.HP
AC = lambda m: m.AC
fort = lambda m: m.fortitude
ref = lambda m: m.reflex
will = lambda m: m.will


def fetch_with_safari(url):
    """This is so we can use Safari's D&DI login cookies"""
    script = """
	tell application "Safari"
        -- activate
        repeat with doc in (every document whose URL contains "compendium")
            tell doc to close
        end repeat
		tell (make new document) to set URL to "%s"
		set doc to 0
		repeat while doc is 0
			try
				set doc to (last document whose URL contains "compendium")
			on error
				delay 0.1
			end try
		end repeat
		set thetext to text of doc
		if thetext contains "Subscribe Now" then
    		tell application "Finder" -- this is so Safari won't block
    		    activate
    		    display dialog "Click Okay when you have logged in to D&DI"
    		end tell
    		set thetext to text of doc
		end if
		tell doc to close
		return thetext
	end tell
    """%url
    p = Popen(['osascript', '-e', script], stdout=PIPE)
    p.wait()
    s = p.stdout.read()
    return s
    
def get_monster(id):
    return fetch_with_safari("http://www.wizards.com/dndinsider/compendium/monster.aspx?id=%i"%id)

def monster_from_string(s,id):
    # s = get_monster(id)
    lines = s.split("\n")
    name = lines[1]
    roles = lines[4]
    defs = re.findall("AC[\W0-9; ]*Fort\w*[\W0-9; ]*Ref\w*[\W0-9; ]*Will\W*[0-9]+", s)[0].replace(';',',')
    hps = re.findall("HP\W*[0-9]+;",s)[0][:-1]
    m = Monster(name, id)
    m.HP = int(hps.split()[1])
    m.defenses = [int(s.split()[1]) for s in defs.split(', ')]
    # print roles
    try:
        _,lvls,rest = roles.split(" ",2)
        m.level = int(lvls)
        m.leader = False
        # m.group=""
        if rest.startswith("Solo") or rest.startswith("Elite"):
            m.group,rest = rest.split(" ",1)
        if "Leader" in rest:
            m.leader = True
            rest = rest.split()[0]
        m.role = rest
    except Exception, e:
        raise e
    return m

def build_monster(id):
    return monster_from_string(get_monster(id),id)
    

def query_monsters(keywords="", max_level=99,min_level=0, role="null", group="null",nameonly=False):
    """Make an XML Query to D&DI's SOAP API"""
    url = root_url + "/KeywordSearchWithFilters?"""
    filters = "%i|%i|null|%s|%s|0|-1|null"%(min_level,max_level,group,role)
    parameters = urlencode(dict(Keywords=keywords, NameOnly=nameonly, Filters=filters,tab="Monster"))
    print url+parameters
    r = urlretrieve(url+parameters)
    with open(r[0]) as f:
        s=f.read()
    return s

def monster_from_xml(element,session=None,update=False):
    """build a monster from the XML entry from the SOAP API"""
    the_id = int(element.find("ID").text)
    name = element.find("Name").text.strip()
    print name,the_id
    m = None
    if session is not None:
        q = session.query(Monster).filter_by(id=the_id)
        m = q.first()
        if m is not None:
            if (not update) or m.level is not None:
                print "already",repr(m)
                return m
    
    s = get_monster(the_id)
    lines = s.split("\n")
    roles = lines[4]
    thename = lines[1]
    # print map(ord, name),map(ord, newname)
    # assert name == newname, "We must have multiple Safari windows active"
    
    hps = re.findall("HP\W*[0-9]+",s)[0]
    s = s[s.find(hps)+len(hps):]
    defs = re.findall("AC.*Will\W*[0-9]+", s)[0].replace(';',',')
    # defs = re.findall("AC[\W0-9; ]*Fort\w*[\W0-9; ]*Ref\w*[\W0-9; ]*Will\W*[0-9]+", s)[0].replace(';',',')
    # print defs
    
    m = m or Monster(thename, the_id)
    m.level = int(element.find("Level").text)
    
    m.HP = int(hps.split()[1])
    m.defenses = [int(s.split()[1]) for s in defs.split(', ')]
    
    m.group = element.find("GroupRole").text.strip()
    
    role = element.find("CombatRole").text.split(',')
    m.role - role[0].strip()
    m.leader = len(g) > 1
    
    if (session):
        session.add(m)
        session.flush()
    return m
    
def download_monsters(keywords="", min_level=0, max_level=99, role="null", group="null",nameonly=False,session=None):
    """download monsters. Can specify keywords, min and max level, role, group, specify name only for keyword search."""
    s = query_monsters(keywords=keywords, max_level=max_level, min_level=min_level, role=role, group=group,nameonly=nameonly)
    root = etree.fromstring(s)
    results = root.find('Results')
    monsters = map(monster_from_xml, results.getchildren(), [session]*len(results.getchildren()))
    return monsters
    



monster_table = Table('monsters', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100), nullable=False),
    Column("AC", Integer),
    Column("fortitude", Integer),
    Column("reflex", Integer),
    Column("will", Integer),
    Column("level", Integer),
    Column("HP", Integer),
    Column("role", String(32)),
    Column("group", String(32)),
    Column("leader", Boolean)
)

monster_mapper = orm.mapper(Monster, monster_table)

class MonsterDB(object):
    """This is the interface to the monster database. The MonsterDB has convenience methods for viewing creatures. See the code littered with '@property'
    for the self expanatory names.
    
    >>> M = MonsterDB(connectDB())
    >>> M.solos # all the solos
    >>> M.controllers # all the controllers
    >>> M.elites.intersect(M.brutes) # all the elite brutes
    
    See m.get for complete query flexibility
    
    """
    @property
    def query(self):
        return self.session.query(Monster)
    
    def __init__(self, engine=None,session=None):
        if engine is None:
            engine = create_engine('sqlite:///:memory:')
        if session is None:
            session = orm.create_session(engine)
        self.session = session
        self.engine = engine
    
    def load_monsters(self, *args, **kwargs):
        """This will download monsters and populate the database. See `download_monsters' for call structure."""
        kwargs.update(session=self.session)
        monsters = download_monsters(*args, **kwargs)
        while monsters:
            self.session.add_all(monsters[:10])
            self.session.flush()
            monsters = monsters[10:]
    
    def drop_monster(self,id):
        """Delete a monster from the database by it's Compendium ID. This is mostly for cleanup during development."""
        m = self.query.filter_by(id=id).first()
        if m:
            self.session.delete(m)
            self.session.flush()
    
    def get(self, *args, **kwargs):
        """A convenience wrapper for M.query. This lets you get any specification of monster.  
        You can get select single values of a key by keyword:
        
        >>> M.get(level=5) to get all level 5 creatures
        >>> M.get(level=11,role="Controller") # all L11 controllers
        
        or you can do more elaborate comparisons by class property:
        
        >>> M.get(Monster.group != 'Minion', Monster.level > 10, Monster.level <= 20, leader=True) 
        
        will get all non-minion Paragon Leaders
        """
        start = self.query
        if kwargs:
            start = start.filter_by(**kwargs)
        for f in args:
            start = start.filter(f)
        return start
    
    @property
    def elites(self):
        return self.query.filter_by(group="Elite")
    
    @property
    def solos(self):
        return self.query.filter_by(group="Solo")
    
    @property
    def standards(self):
        return self.query.filter_by(group="Standard")
    
    @property
    def minions(self):
        return self.query.filter_by(group="Minion")
    
    @property
    def skirmishers(self):
        return self.query.filter_by(role="Skirmisher")
    
    @property
    def soldiers(self):
        return self.query.filter_by(role="Soldier")
    
    @property
    def artillery(self):
        return self.query.filter_by(role="Artillery")
    
    @property
    def brutes(self):
        return self.query.filter_by(role="Brute")
    
    @property
    def controllers(self):
        return self.query.filter_by(role="Controller")
    
    @property
    def leaders(self):
        return self.query.filter_by(leader=True)
    
    @property
    def groups(self):
        return [self.minions, self.standards, self.elites, self.solos]
    
    @property
    def roles(self):
        return [self.artillery, self.brutes, self.controllers, self.skirmishers, self.soldiers]
    
    @property
    def all(self):
        return self.query.all()
    
    
    def levels(self,levels):
        """return all monsters in a set of levels"""
        if isinstance(levels, int):
            return self.query.filter_by(level=levels)
        return self.query.filter(Monster.level in levels)
    
    def by_role(self,group):
        """Split a group into groups for each role. starting must still be in query form, not a list.
        Returns 5 groups, alphabetically: art,brut,con,skir,sol
        
        >>> M.by_role(M.solos)
        will return the solos in each of the roles.
        """
        return [ group.intersect(g) for g in (self.artillery, self.brutes, self.controllers, self.skirmishers, self.soldiers) ]
    
    # def add

def connectDB(fname='monsters.db'):
    # f = resolve_file_path(fname)
    do_init = not os.path.exists(fname)
    engine = create_engine('sqlite:///%s'%fname)
    # metadata.bind(engine)
    metadata.create_all(engine, checkfirst=True)
    return engine


# plotting functions

def plot_groups(key, *groups):
    """Plot a single value versus level for a number of groups of monsters. Each group will be plotted as a different color
    Keys are: AC, fort, reflex, will
    >>> M = MonsterDB(connectDB())
    >>> plot(AC,M.solos,M.elites,M.standards) 
    >>> plot(reflex, M.leaders, M.levels(range(5)))
    
    You can also define any function that returns a number:
    >>> def maxdef(m): return max(m.AC, m.reflex,m.fortitude,m.will)
    >>> plot_groups(maxdef, M.get(role="Skirmisher",Monster.level < 11))
    this will plot the highest defense for all Heroic tier skirmishers
    
    
    """
    eps = .6/(len(groups))
    off=-.3+eps
    figure()
    grid(True)
    pylab.xlabel("Level")
    for g in groups:
        plot([m.level + off for m in g], [key(m) for m in g], 'o',alpha=0.4)
        off+=eps


def plot_defenses(*groups):
    """Plot all defenses versus level for some number of groups of monsters.
    Defenses are offset and colored.
    Points are transparent, so light dots represent outliers, and dark ones are common values.
    """
    # eps = .6/(len(groups))
    eps = 0.16
    colors = "krgb"
    figure()
    grid(True)
    pylab.xlabel("Level")
    for i,g in enumerate(groups):
        off=-.24
        for i,d in enumerate("AC fortitude reflex will".split()):
            plot([m.level + off for m in g], [getattr(m,d) for m in g], colors[i]+'o',alpha=0.25)
            off+=eps
    legend("AC Fort Ref Will".split(), loc=0).get_frame().set_alpha(0.75)

def defense_hist(group):
    """Makes aligned histograms for each defense for a group of monsters.
    Useful for comparing high/low defenses.
    
    # defenses for all non-minion L8s:
    >>>defense_hist(M.get(Monster.group != 'Minion', level=8)) 
    
    >>>de
    
    """
    data = array([m.defenses for m in group])
    AC,fort,ref,will=data.transpose()
    xmin = data.min()
    xmax = data.max()
    # bins = 
    print xmin,xmax
    def do_hist(x,**kwargs):
        hist(x, bins=xmax-xmin,range=(xmin,xmax),**kwargs)
        pylab.xlim(xmin,xmax)
        pylab.yticks([])
        pylab.grid(True)
    
    figure()
    subplot(411)
    do_hist(AC,facecolor="k",edgecolor="w")
    pylab.ylabel("AC")
    
    subplot(412)
    do_hist(fort,facecolor="r")
    pylab.ylabel("Fort")
    
    subplot(413)
    do_hist(ref,facecolor="g")
    pylab.ylabel("Reflex")
    
    subplot(414)
    do_hist(will,facecolor="b")
    pylab.ylabel("Will")
    

def plot_roles(group,M):
    """This splits a group into each role, and plots the number of creatures in the group that occupy each role.
    Must pass a MonsterDB object, so it can split the group into roles."""
    gps = M.by_role(group)
    figure()
    bar(arange(5), [g.count() for g in gps])
    xticks(numpy.arange(5)+.4, "Artillery Brute Controller Skirmisher Soldier".split())
    