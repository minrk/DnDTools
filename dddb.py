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
pjoin = os.path.join
from subprocess import Popen, PIPE
from string import printable
from random import randint
from getpass import getpass

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

try:
    import twill
    from BeautifulSoup import BeautifulSoup
except:
    twill = None

from sqlalchemy import *
from sqlalchemy import orm

metadata = MetaData()

root_url = "http://www.wizards.com/dndinsider/compendium/compendiumSearch.asmx"
_agent = None

def unescape(s):
    s = s.replace("\xe2\x80\x99","'")
    return "".join([ c for c in s if c in printable ])

roles = "Artillery Brute Controller Lurker Skirmisher Soldier".split()
groups = "Minion Standard Elite Solo".split()

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
        s += "\n    Compendium ID #%i"%self.id
        return s
    def __repr__(self):
        return "< %s: Level %i %s >"%(self.name, self.level, self.group or self.role)
    
    def view(self):
        url = "http://www.wizards.com/dndinsider/compendium/monster.aspx?id=%i"%self.id
        print url
        if sys.platform == "darwin":
            os.system("open %s"%url)
        else:
            pass

thecolors = "bgrcmyk"
# sorting keys
level = lambda m: m.level
HP = lambda m: m.HP
AC = lambda m: m.AC
fort = lambda m: m.fortitude
ref = lambda m: m.reflex
will = lambda m: m.will
alldef = lambda m: mean(m.defenses)
flatdef = lambda m: mean(m.defenses) - m.level # this should come out flat when plotted vs level
lifetime = lambda m: m.HP * flatdef(m)
better_life = lambda m: m.HP * ( mean(m.defenses) - .9*m.level-4)

to_hit = lambda m: mean([m.AC-2, m.fortitude, m.reflex, m.will]) - 4 - m.level/2 - (m.level+3)/5 - m.level/8 - (m.level+5)/10

# Basic AC roll, assume +2 Proficiency, 18 starting skill, weapon at-level, weapon focus
#                        prof base level/2      weapon        skill train   expertise
hit_AC = lambda m: m.AC - ac_bonus(m.level)
# for the Rev:
hit_ref = lambda m: m.reflex - rev_bonus(m.level)
hit_fort = lambda m: m.fortitude - rev_bonus(m.level)

rev_bonus = lambda level:     4 + level/2 + (level+2)/5 + (level+4)/8 + (level+5)/10
ac_bonus = lambda level:  2 + 4 + level/2 + (level+2)/5 + (level)/8 + (level+5)/10

# hit_X is what you have to roll (+ proficiency-2 and feat bonusus) to hit, 
        # assuming you start with 18 in relevant skill, put 1 in the skill each 4th level, 
        # and get a new weapon at the third level of your half-tier (+1 for L3-7, +2 for L8-12, etc.)
        # and have Weapon/Implement Expertise by level 5

tierHP = lambda level: 20+4.5*level*255/30

def outliers(M, group, keys=None,gap=None):
    liers = set()
    if keys is None:
        keys = [HP,AC,fort,ref,will]
    else:
        if not iterable(keys):
            keys = [keys]
    for lvl in set(map(level, group)):
        subgroup = group.intersect(M.level(lvl))
        for key in keys:
            values = map(key, subgroup)
            trim = max(len(values)/10,2)
            # print trim
            for i in range(trim):
                values and values.remove(max(values))
                values and values.remove(min(values))
            if values:
                vmax = max(values)
                vmin = min(values)
                for m in subgroup:
                    v = key(m)
                    if v > vmax+vmax/10:
                        liers.add(m)
                    if v < vmin-vmin/10:
                        liers.add(m)
                
            else:
                pass
                # print "empty set for level %i with key %s"%(lvl,key)
    return liers
            

def fetch_with_safari(url):
    """This is so we can use Safari's D&DI login cookies"""
    script = """
	tell application "Safari"
    	-- activate
    	repeat with doc in (every document whose URL contains "compendium")
    		tell doc to close
    	end repeat
    	set doc to (make new document with properties {URL:"%s"})
    	set doc to 0
    	repeat while doc is 0
    		try
    			set doc to (last document whose URL contains "compendium")
    		on error
    			delay 0.1
    		end try
    	end repeat
    	set thetext to text of doc
    	repeat while thetext does not contain "Subscribe Now" and thetext does not contain "Published"
    		delay 0.1
    		set thetext to text of doc
    	end repeat
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

def fetch_with_twill(url):
    global _agent
    if _agent is None:
        _agent = twill.get_browser()
    a = _agent
    a.go(url)
    while a.get_url() != url:
        f = a.get_form('form1')
        f['email'] = raw_input("D&D Insider Email: ")
        f['password'] = getpass("Password: ")
        twill.commands.submit()
        a.go(url)
    
    return a.get_html()
        
    
def get_monster(id):
    url = "http://www.wizards.com/dndinsider/compendium/monster.aspx?id=%i"%id
    if twill:
        return monster_from_html(fetch_with_twill(url),id)
    elif sys.platform == 'darwin':
        return monster_from_string(fetch_with_safari(url),id)
    else:
        raise "I can't fetch the url, please install twill and BeautifulSoup"

def _extract_value(parent,name):
    e = parent.find('b',text=name)
    return int(re.findall('[0-9]+',e.next)[0])

def monster_from_html(s,id):
    soup = BeautifulSoup(s)
    soup = soup.find('div', id='detail')
    h1 = soup.find('h1',{'class':'monster'})
    header = list(h1.childGenerator())
    name = header[0].encode('utf8')
    span = h1.find('span', {'class':'level'})
    roles = list(span.childGenerator())[0]
    body = soup.find('table',{'class':'bodytable'})
    if body is None:
        body = soup.find('p',{'class':'flavor'})
    m = Monster(name, id)
    
    m.HP = _extract_value(body,'HP')
    m.defenses = [_extract_value(body,d) for d in 'AC Fortitude Reflex Will'.split()]
    
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
    
    new_m = get_monster(the_id)
    m = m or new_m
    m.level = int(element.find("Level").text)
    
    m.HP = new_m.HP
    m.defenses = new_m.defenses
    
    m.group = element.find("GroupRole").text.strip()
    
    role = element.find("CombatRole").text.split(',')
    print role, m.group
    m.role = role[0].strip()
    m.leader = len(m.group) > 1
    
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
        elif isinstance(engine, basestring):
            engine = connectDB(engine)
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
    def lurkers(self):
        return self.query.filter_by(role="Lurker")
    
    @property
    def leaders(self):
        return self.query.filter_by(leader=True)
    
    @property
    def groups(self):
        return [self.minions, self.standards, self.elites, self.solos]
    
    @property
    def roles(self):
        return [self.artillery, self.brutes, self.controllers, self.lurkers, self.skirmishers, self.soldiers]
    
    @property
    def random(self):
        idx = randint(0,self.query.count()-1)
        return self.all[idx]
    
    @property
    def all(self):
        return self.query
    
    
    
    def level(self,levels):
        """return all monsters in a set of levels or single level. Takes an integer or container of integers"""
        if isinstance(levels, int):
            return self.query.filter_by(level=levels)
        return self.query.filter(Monster.level in levels)
    
    def by_role(self,group=None):
        """Split a group into groups for each role. starting must still be in query form, not a list.
        Returns 5 groups, alphabetically: art,brut,con,skir,sol
        
        >>> M.by_role(M.solos)
        will return the solos in each of the roles.
        
        Defauts to starting from M.all, if group not specified
        """
        if group is None:
            group = self.all
        return [ group.intersect(g) for g in self.roles ]
    
    def by_group(self,group=None):
        """Split a group into groups for each Group Role (Solo, Minion, etc.). starting must still be in query form, not a list.
        Returns 4 groups, by size: minion, standard, elite, solo
        
        >>> M.by_group(M.skirmishers)
        will return the skirmishers in each of the group roles.
        
        Defauts to starting from M.all, if group not specified
        """
        if group is None:
            group = self.all
        return [ group.intersect(g) for g in self.groups ]
    
    def search(self, keywords, strict=False):
        """
        If strict: do substring match on names
        else: do unordered keyword search
        default: not strict"""
        q = self.query
        if strict:
            q = q.filter(Monster.name.like("%%%s%%"%keywords))
        else:
            for word in keywords.split():
                q = q.filter(Monster.name.like("%%%s%%"%(word)))
                print q.count()
        return q
    
    # def add

def connectDB(fname='monsters.db'):
    # do_init = not os.path.exists(fname)
    engine = create_engine('sqlite:///%s'%fname)
    metadata.create_all(engine, checkfirst=True)
    return engine

######################################################
# plotting functions
######################################################

def plot_groups(key, *groups):
    """Plot a single value versus level for a number of groups of monsters. Each group will be plotted as a different color
    Keys are: AC, fort, reflex, will
    >>> M = MonsterDB(connectDB())
    >>> plot(AC,M.solos,M.elites,M.standards) 
    >>> plot(reflex, M.leaders, M.level(range(5)))
    
    You can also define any function that returns a number:
    >>> def maxdef(m): return max(m.AC, m.reflex,m.fortitude,m.will)
    >>> plot_groups(maxdef, M.get(role="Skirmisher",Monster.level < 11))
    this will plot the highest defense for all Heroic tier skirmishers
    
    
    """
    
    eps = .6/(len(groups))
    off=-.3+eps
    if len(groups) == 1:
        off=0
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

def defense_hist(group,title=""):
    """Makes aligned histograms for each defense for a group of monsters.
    Useful for comparing high/low defenses.
    
    # defenses for all non-minion L8s:
    >>>defense_hist(M.get(Monster.group != 'Minion', level=8)) 
    
    
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
    pylab.title(title)
    
    subplot(412)
    do_hist(fort,facecolor="r")
    pylab.ylabel("Fort")
    
    subplot(413)
    do_hist(ref,facecolor="g")
    pylab.ylabel("Reflex")
    
    subplot(414)
    do_hist(will,facecolor="b")
    pylab.ylabel("Will")
    if isinstance(group,orm.Query):
        count = group.count()
    else:
        count = len(group)
    pylab.xlabel("%i total"%count)

def plot_by_role(group,M):
    """This splits a group into each role, and plots the number of creatures in the group that occupy each role.
    Must pass a MonsterDB object, so it can split the group into roles."""
    gps = M.by_role(group)
    figure()
    bar(arange(len(gps)), [g.count() for g in gps],color=thecolors[:len(gps)])
    xticks(numpy.arange(len(gps))+.4, roles)

def plot_by_group(group,M):
    """This splits a group into each group role, and plots the number of creatures in the group that occupy each role.
    Must pass a MonsterDB object, so it can split the group into roles."""
    gps = M.by_group(group)
    figure()
    bar(arange(len(gps)), [g.count() for g in gps],color='cbgr')
    xticks(numpy.arange(len(gps))+.4, groups)

def plot_counts(M, groups, names=None):
    levels = range(1,31)
    figure()
    off=0
    colors = thecolors[:len(groups)]
    grid(True)
    gcf().set_figwidth(16)
    w = 1./(len(groups)+1)
    if names is None:
        names = [None]*len(groups)
    for c,group,name in zip(colors, groups, names):
        # print group
        heights = [group.intersect(M.level(i)).count() for i in levels]
        # print heights
        bar(array(levels)+off, heights,width=w, facecolor=c,label=name)
        off += w
    if names[0] is not None:
        legend(loc=0)
    xticks(array(levels), ["      %i"%l for l in levels])
    xlim(1,31)
    xlabel("Level")
    
def mean_key(key, group):
    """returns the mean of the key for each level. Good for translating scatter plot data to lines."""
    return array([ mean([ key(m) for m in group.filter_by(level=i) ]) for i in range(1,31)] )

def plot_group_lines(key, *groups):
    figure()
    grid(True)
    pylab.xlabel("Level")
    for g in groups:
        plot(range(1,31), mean_key(key,g))


def plot_all_levels(M,root="/Volumes/zino/www/DandD/dddb/levels"):
    for level in range(1,31):
        gp = M.level(level)
        defense_hist(gp, "All Level %i"%(level))
        savefig(pjoin(root, "L%i.png"%level))
        close()

legend_roles = lambda : legend(roles, loc=0).get_frame().set_alpha(0.75)
legend_groups = lambda : legend(groups, loc=0).get_frame().set_alpha(0.75)