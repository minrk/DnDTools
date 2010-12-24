#!/usr/bin/env python
"""Simple Python script to generate iCalendar from the D&D content calendar.
This depends on BeautifulSoup and icalendar, both of which are easy_install-able."""

import urllib2
from BeautifulSoup import BeautifulSoup
from datetime import date, timedelta
from icalendar import Event, Calendar


base_url = "http://www.wizards.com/dnd/"
calendar_url = base_url + "calendar.aspx?Month=%0i&Year=%i"
first_month = (9,2009) # the first month with data

oneday = timedelta(days=1)

def event_from_row(row_soup, day):
    """Parse a CalendarEventRow into an iCalendar Event."""
    ev = Event()
    ev.add('dtstart', day)
    ev.add('dtend', day+oneday)
    insider = row_soup.find('img', {'class' : 'CalendarDnDIImage'}) is not None
    prefix = ""
    span = row_soup.find('span', {'class' : 'CalendarPrefix'})
    if span is not None:
        prefix += span.contents[0] + ' '
    a = row_soup.find('a', {'class' : 'CalendarEvent'})
    if a is not None:
        url = base_url + a['href']
        ev.add("url", url)
        ev.add("description", url)
    else:
        a = row_soup.find('a', {'class' : 'CalendarEventNoLink'})
    
    title = a.contents[0]
    ev.add("summary", prefix+title)
    return ev

def events_from_day(day_soup, month, year):
    """Generate a list of events from a CalendarCell element (a single day)."""
    daydiv = day_soup.find('div', {'class' : 'CalendarDay'})
    span = daydiv.find('span')
    days = int(span.contents[0])
    day = date(year, month, days)
    event_rows = day_soup.findAll('div', {'class' : 'CalendarEventRow'})
    events = []
    for i,row in enumerate(event_rows):
        try:
            ev = event_from_row(row, day)
        except:
            print row
            raise
        else:
            ev['uid'] = "%s-%i"%(str(day),i)
            events.append(ev)
            
    return events

def scrape_month(month,year):
    """Scrape the calendar page for a month, and return a list of all Events.
    in that month."""
    print "Scraping %02i/%i"%(month,year)
    url = calendar_url%(month,year)
    req = urllib2.urlopen(url)
    if req.getcode() != 200:
        raise "Failed to fetch, error %i"%req.getcode()
    raw = req.read()
    soup = BeautifulSoup(raw)
    caldiv = soup.find('div', {'class':'CalendarContent'})
    days = caldiv.findAll('div', {'class':'CalendarCell'})
    events = []
    for day in days:
        events.extend(events_from_day(day, month, year))
    return events

def generate_calendar(start=first_month, months=-1):
    """Generate an iCalendar containing all events on the D&D Content Calendar.
    Default behavior will get all data ever, but it can be limited by the start
    and months arguments."""
    cal = Calendar()
    cal.add('X-WR-CALNAME', 'D&D Content')
    m,y = start
    months = int(months)
    while months != 0:
        events = scrape_month(m,y)
        months -= 1
        if not events:
            print "No events for %02i/%i"%(m,y)
            break
        for ev in events:
            cal.add_component(ev)
        m += 1
        if m == 13:
            m = 1
            y += 1
    return cal

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        outfile = sys.argv[1]
    else:
        outfile = None
    cal = generate_calendar()
    if outfile:
        with open(outfile, 'w') as f:
            f.write(cal.as_string())
    else:
        print cal.as_string()
    