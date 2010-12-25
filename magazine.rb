#!/usr/bin/env ruby
# a script for downloading the D&D magazines from the websites

require 'rubygems'
require 'mechanize'
require 'highline/import'

# prompt for login
email = ask("D&D Insider Email: ") {|q| q.echo=true }
pwd =   ask("         Password: ") {|q| q.echo='*' }

agent = Mechanize.new
# get the login page
agent.get('http://www.wizards.com/dndinsider/compendium/login.aspx?page=paragonpath&id=273') do |page|
  # Submit the login form
  newpage = page.form_with(:name => 'form1') do |f|
    f['email']  = email
    f['password'] = pwd
  end.click_button
  if newpage.title == nil
    puts "failed login"
    exit -1
  else
    puts "logged in"
  end
end
# now we are logged in (?!)

def fetch_issue(page, filename)
  link = page.link_with(:href => /downloads/)
  if link == nil
    puts "No link found for #{filename}"
    return
  else
    puts "fetching #{filename}"
    pdf = link.click
    pdf.save_as(filename)
  end
end

def fetch_magazine(agent,name,limit)
  name = name.downcase
  url="http://www.wizards.com/dnd/issues.aspx?category=#{name}"
  caps = name[0,1].upcase + name[1,name.length]
  puts "downloading #{caps} back to issue #{limit}"
  agent.get(url) do |page|
    links = page.links_with(:text => /#[0-9]+/)
    links.each do |link|
      issue = link.text.match(/[0-9]+/).to_s.to_i
      fname = "#{caps} ##{issue}.pdf"
      if issue > limit
        if Dir.entries('.').detect {|f| f==fname}
          puts "already have #{fname}"
        else
          page = link.click
          fetch_issue(page, fname)
        end
      else
        puts "stopping at #{fname}"
        return
      end
    end
  end
end

# now get the issue listing:
if ARGV.length == 2
  min_dungeon = ARGV[0].to_i
  min_dragon = ARGV[1].to_i
else
  min_dungeon = min_dragon = 1
end
fetch_magazine(agent,'dungeon', min_dungeon)
fetch_magazine(agent,'dragon', min_dragon)