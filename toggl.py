#!/usr/bin/python

import sys, os, io, getpass, json, urllib2, datetime

def get_api_key(username, password):
	user_data = "Basic " + (username + ":" + password).encode("base64").rstrip()

	request = urllib2.Request("https://www.toggl.com/api/v8/me",
				headers = { 'Accept': 'application/json', 'Authorization': user_data }
			)

	result = urllib2.urlopen(request)
	d = json.loads(result.read())

	api_token = d['data']['api_token']
	return api_token


def get_workspaces(key):
	user_data = "Basic " + (key + ":api_token").encode("base64").rstrip()

	request = urllib2.Request("https://www.toggl.com/api/v8/workspaces",
				headers = { 'Accept': 'application/json', 'Authorization': user_data }
			)

	result = urllib2.urlopen(request)
	d = json.loads(result.read())

	return d


def get_workspace_projects(key, workspace):
	user_data = "Basic " + (str(key) + ":api_token").encode("base64").rstrip()

	request = urllib2.Request("https://www.toggl.com/api/v8/workspaces/"+str(workspace)+"/projects",
				headers = { 'Accept': 'application/json', 'Authorization': user_data }
			)

	result = urllib2.urlopen(request)
	d = json.loads(result.read())

	return d


# curl -v -u 1971800d4d82861d8f2c1651fea4d212:api_token \
#     -H "Content-Type: application/json" \
#     -d '{"time_entry":{"description":"Meeting with possible clients","tags":["billed"],"pid":123,"created_with":"curl"}}' \
#     -X POST https://www.toggl.com/api/v8/time_entries/start

{"time_entry": {"pid": "8570687", "description": "test", "created_with": "bretts_toggl_tool"}}

def start_time_for_project(key, project, description):
	user_data = "Basic " + (str(key) + ":api_token").encode("base64").rstrip()

	post_data = json.dumps({
					"time_entry": {
						"description": description,
						"pid": project,
						"created_with": "bretts_toggl_tool" 
					}
				});

	request = urllib2.Request("https://www.toggl.com/api/v8/time_entries/start",
				headers = { 'Accept': 'application/json', 'Authorization': user_data, 'Content-Type': 'application/json' },
				data = post_data
			)

	result = urllib2.urlopen(request)
	d = json.loads(result.read())

	return d


def stop_time_for_project(key, time_entry_id):
	user_data = "Basic " + (str(key) + ":api_token").encode("base64").rstrip()

	request = urllib2.Request("https://www.toggl.com/api/v8/time_entries/"+str(time_entry_id)+"/stop",
				headers = { 'Accept': 'application/json', 'Authorization': user_data, 'Content-Type': 'application/json' }
			)

	request.get_method = lambda: 'PUT'

	result = urllib2.urlopen(request)
	d = json.loads(result.read())

	return d


def read_config():
	fd = open(".toggl-info", "r")
	lines = fd.readlines()

	values = {}

	for line in lines:
		parts = line.split("=")

		if len(parts) == 2:
			values[parts[0]] = parts[1].rstrip()

	return values

def print_help():
	print "TOGGL command line (because UIs suck)"
	print "-------------------------------------"
	print "init\t\t intializes directory with project and workspace id"
	print "start\t\t starts the timer given a work title"
	print "stop\t\t stops the timer if work was started"


def do_init(args):
	username = raw_input("Toggl Username: ")
	password = getpass.getpass("Toggl Password: ")

	api_token = get_api_key(username, password)
	workspaces = get_workspaces(api_token)
	workspace_id = workspaces[0]["id"]

	if len(workspaces) > 1:
		print "You are part of more than one workspace."

		count = 0
		for wsp in workspaces:
			print str(count) + ": " + wsp["name"]
			count += 1

		w = int(raw_input("Choose a workspace: ").rstrip())
		workspace_id = workspaces[w]["id"]


	projects = get_workspace_projects(api_token, workspace_id)
	project_id = projects[0]["id"]

	if len(projects) > 1:
		print "There are a bunch of projects to choose from."

		count = 0
		for prj in projects:
			print str(count) + ": " + prj["name"]
			count += 1

		p = int(raw_input("Choose project: ").rstrip())
		project_id = projects[p]["id"]


	fd = open(".toggl-info", "w+")
	fd.write("username="+username+"\n")
	fd.write("api_token="+str(api_token)+"\n")
	fd.write("workspace="+str(workspace_id)+"\n")
	fd.write("project="+str(project_id)+"\n")
	fd.close()


def do_start(args):
	if os.path.exists(".toggl-working"):
		print "Already working. You have to stop your working task first"

	config = read_config()
	d = start_time_for_project(config["api_token"], config["project"], args[0])
	print d

	fd = open(".toggl-working", "w+")
	fd.write(str(d["data"]["id"]))
	fd.close()

	print "started work: (" + str(d["data"]["id"]) + ") " + str(d["data"]["description"])


def do_stop(args):
	config = read_config()

	fd = open(".toggl-working", "r")
	time_entry = str(fd.readlines()[0].rstrip())
	fd.close()

	d = stop_time_for_project(config["api_token"], time_entry)

	print "Stopped '" + str(d["data"]["description"]) + "'. You worked for: " + str(d["data"]["duration"]/60.0) + " minutes"

	os.remove(".toggl-working")

def do_time(args):
	pass

commands = {
	"init": do_init,
	"start": do_start,
	"stop": do_stop,
}

if len(sys.argv) < 2:
	print_help()

try:
	commands[sys.argv[1]](sys.argv[2:])

except KeyError:
	print_help()
	


