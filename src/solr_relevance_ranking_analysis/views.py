from django.shortcuts import render

from django.http import HttpResponse 
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django import forms

import json
import requests
import os.path


class SearchForm(forms.Form):

	query = forms.CharField(widget=forms.TextInput, label="Solr request URL (full Solr select query)", required=False)


# filter inactive children of "max of"
def maxof(data, results = [], parent=0, max_of_value = 0):

	for entry in data:

		if entry['parentline'] == parent:

			max_of = False
			if 'type' in entry:
				if entry['type'] == "max":
					max_of = True

			if entry['numvalue'] >= max_of_value:

				results.append(entry)

				# recursive analysis of children
				if max_of:
					data, results = maxof(data, results, parent=entry['linenumber'], max_of_value=entry['numvalue'])
				else:
					data, results = maxof(data, results, parent=entry['linenumber'], max_of_value=0)

	return data, results


def scale_score(fullsize, value, maxvalue):

	scaled = round( fullsize/maxvalue * ( value ), 0)

	# print ('full: {}, value: {}, maxvalue: {}, scaled: {}'.format(fullsize, value, maxvalue, scaled))

	return scaled


def get_scorevalues(data, linenumber):

	boost = None
	idf = None
	tfNorm = None

	#get linenumber of score child
	scorelinenumber = None
	for entry in data:
		if 'type' in entry:
			if entry['type'] == 'score' and entry['parentline'] == linenumber:
				scorelinenumber = entry['linenumber']

	if scorelinenumber:
		for entry in data:

			if 'type' in entry:
				if entry['type'] == 'boost' and entry['parentline'] == scorelinenumber:
					boost = entry['boost']

				if entry['type'] == 'tfNorm' and entry['parentline'] == scorelinenumber:
					tfNorm = entry['tfNorm']

				if entry['type'] == 'idf' and entry['parentline'] == scorelinenumber:
					idf = entry['idf']

	return boost, idf, tfNorm


def summarize(nodes, fields, maxscore):

	summarization = []

	score = nodes[0]['numvalue']
        
	summarized_score = 0

	for node in nodes:

		if 'type' in node:
			
			if node['type'] == 'weight':

				summarized_score += node['numvalue']

				boost, idf, tfNorm = get_scorevalues(nodes, node['linenumber'])
				data = {}
				data['term'] = node['term']
				data['fieldname'] = node['fieldname']

				fieldname = node['fieldname']
				if fieldname in fields:
					data['fieldcolor'] = fields[fieldname]['color']

				data['score'] = round( node['numvalue'], 2)
				data['score_scaled'] = scale_score(fullsize=800, value=node['numvalue'], maxvalue=maxscore)
				data['boost'] = boost
				data['idf'] = idf
				data['tfNorm'] = tfNorm

				summarization.append(data)

			if node['type'] == 'FunctionQuery':

				summarized_score += node['numvalue']

				data = {}
				data['term'] = node['function_query']
				data['fieldname'] = 'FunctionQuery'

				fieldname = node['function_query']
				if fieldname in fields:
					data['fieldcolor'] = fields[fieldname]['color']
				data['score'] = round( node['numvalue'], 2)
				data['score_scaled'] = scale_score(fullsize=800, value=node['numvalue'], maxvalue=maxscore)

				summarization.append(data)


	#if round(summarized_score,4) < round(score,4):
	#summarization.append( "\n\nWarning: This summarization does not include all scoring factors, since more complex ranking f.e. by additioal functions like custom boostfunction(s). Please analyze all weights by tree view.\n" )
	#summarization.append( "Summarized score of full score: Only {} of {} summarized".format(summarized_score, score) )


	return summarization


def summarize_fields(nodes,fields={}):

	colors = ['#FF8C00', '#E9967A', '#B8860B', '#8B008B', '#8FBC8F', '#483D8B', '#00CED1', '#9400D3', '#B22222', '#DAA520', '#FF69B4', '#FFFFFF']

	for node in nodes:
		if 'type' in node:
			if not 'inactive' in node:
				if node['type'] == 'weight':
	
					fieldname = node['fieldname']
					if not fieldname in fields:
	
						fields[fieldname] = {}
	
						boost, idf, tfNorm = get_scorevalues(nodes, node['linenumber'])
						
						if boost == None:
							boost = 1
	
						fields[fieldname]['boost'] = boost
						
						colorindex = len(fields)-1
						if colorindex > len(colors)-1:
							colorindex = len(colors)-1
	
						fields[fieldname]['color'] = colors[colorindex]
						
				if node['type'] == 'FunctionQuery':
	
					fieldname = node['function_query']
					if not fieldname in fields:
	
						fields[fieldname] = {}
	
						colorindex = len(fields)-1
						if colorindex > len(colors)-1:
							colorindex = len(colors)-1
	
						fields[fieldname]['color'] = colors[colorindex]

	return fields


def index(request):

	# default settings, do not edit here, use the config file
	config = {
				'solr': ['http://localhost:8983/solr/'] 
			}

	# read config from config file
	configfilename = '/etc/opensemanticsearch/apps/relevance_ranking_analysis/config.json'
	if os.path.isfile(configfilename):
		
		f = open(configfilename)
		config = json.load(f)
		f.close()


	form = SearchForm(request.GET) # A form bound to the POST data
	if form.is_valid():
		query = form.cleaned_data['query']

	# prevent misuse as HTTP proxy:
	allowed = False
	
	# if empty query, allow access to empty form
	if not query:
		allowed = True

	# check if URI / Solr server / core is accessable
	for server in config['solr']:
		if query.startswith(server):
			allowed = True

	if not allowed:
		raise PermissionDenied


	numFound = None
	docs = None
	explain = None
	querystring = None
	parsed_query = None
	count_docs = 0
	fields = None
	boostfuncs = None
	boost_queries = None
	parsed_boost_queries = None
	filter_queries = None
	parsed_filter_queries = None
	timing = None

	if query:

		url = query
		if not "debugQuery=on" in url:
			url += "&debugQuery=on"

		#response = requests.get(url, params = params)

		response = requests.get(url)

		r = response.json()

		count_docs = len(r['response']['docs'])
		
		numFound = r['response']['numFound']
		
		explain = r['debug']['explain']
    	
    	
    	
		parsed_query = r['debug']['parsedquery']

		if 'querystring' in r['debug']:
			querystring = r['debug']['querystring']
		
		if 'boostfuncs' in r['debug']:
			boostfuncs = r['debug']['boostfuncs']
		
		if 'boost_queries' in r['debug']:
			boost_queries = r['debug']['boost_queries']
		if 'parsed_boost_queries' in r['debug']:
			parsed_boost_queries = r['debug']['parsed_boost_queries']

		if 'filter_queries' in r['debug']:
			filter_queries = r['debug']['filter_queries']
		if 'parsed_filter_queries' in r['debug']:
			parsed_filter_queries = r['debug']['parsed_filter_queries']

		if 'timing' in r['debug']:
			timing = json.dumps(r['debug']['timing'], indent=4)
		
		fields={}
		docs=[]
		maxscore = 0
    
		for doc in r['response']['docs']:
			
			nodes = []
    	
			last_indent = 0
			parentline = 0
			docexplain = explain[doc['id']]
			docexplain = docexplain.replace("\n)", ")")
			linenumber = 0
			last_parent = {}
    	    
			for line in docexplain.split("\n"):
    	        
				linenumber += 1 
    			
				if line:
    				
					indent = len(line) - len(line.lstrip(' '))
					line = line.lstrip(' ')
    	
					data = {}
    	            
					data['linenumber'] = linenumber
    	            
					data['text'] = line
    	            
					data['numvalue'] = float( line[ 0 : line.find(" = ") ] )
    				
					if line.endswith(' = boost'):
						data['type'] = 'boost'
						data['boost'] = data['numvalue']
    	
					if ' = idf' in line:
						data['type'] = 'idf'
						data['idf'] = data['numvalue']
    	
					if ' = tfNorm' in line:
						data['type'] = 'tfNorm'
						data['tfNorm'] = data['numvalue']
    				
					if line.endswith(' = max of:'):
						data['type'] = 'max'
    					
					if ' = score' in line:
						data['type'] = 'score'
						
					if ' = FunctionQuery' in line:
						data['type'] = 'FunctionQuery'
						prefix = ' = FunctionQuery('
						data['function_query'] = line[line.find(prefix)+len(prefix) : line.rfind(')') ]
    
					if ' = weight(' in line:
    	                
						data['type'] = 'weight'

						if ' = weight(Synonym(' in line:
							prefix = ' = weight(Synonym('
							data['fieldname'] = line[line.find(prefix)+len(prefix) : line.find(':') ]
    					
							data['term'] = line[ line.find(':')+1 : line.rfind(') in ') ]
							# change further fieldnames from multiple terms (synonyms) to separator
							data['term'] = data['term'].replace(' ' + data['fieldname'] + ':', ' | ')

						else:
							prefix = ' = weight('
							data['fieldname'] = line[line.find(prefix)+len(prefix) : line.find(':') ]
    					
							data['term'] = line[ line.find(':')+1 : line.rfind(' in ') ]
    
    
					#is child					
					if indent > last_indent:
						parentline = linenumber - 1
						last_parent[indent] = parentline
					if indent < last_indent: # last parent on upper level in indent hierarchy
						parentline = last_parent[indent]
    					
					last_indent = indent
    	
					data['parentline'] = parentline
    	            
					nodes.append(data)
    
			score = nodes[0]['numvalue']
			if score > maxscore:
				maxscore = score
    	
			# set children after the first child of max of to inactive            
			analyzed_data, analyzed_results = maxof(data = nodes, results=[], parent=0)
			
			# get fields overview/weights
			fields = summarize_fields(nodes=analyzed_results, fields=fields)
			
			# summarize document values
			doc_summarization = summarize(analyzed_results, fields, maxscore)
    
			doc_analysis = {}
    
			doc_analysis['id'] = doc['id']
			doc_analysis['summarization'] = doc_summarization
    
			doc_analysis['score'] = round(score ,2)
			doc_analysis['explain'] = docexplain

			# document title
			doc_analysis['title_field'] = None
			doc_analysis['title'] = None

			if 'title_fields' in config:
				for title_field in config['title_fields']:
					if title_field in doc:
						doc_analysis['title_field'] = title_field
						doc_analysis['title'] = doc[title_field]
						break
			
			docs.append(doc_analysis)
    
	return render(request, 'solr_relevance_ranking_analysis/solr_relevance_ranking_analysis.html', 
    		{
    			"numFound": numFound,
    			"docs": docs,
    			"explain": explain,
    			"query": query,
    			"querystring": querystring,
    			"parsed_query": parsed_query,
    			"boostfuncs": boostfuncs,
				"boost_queries": boost_queries,
				"parsed_boost_queries": parsed_boost_queries,
				"filter_queries": filter_queries,
				"parsed_filter_queries": parsed_filter_queries,
				"timing": timing,
    			"count_docs": count_docs,
    			"form": form,
                "fields": fields,
    		})
