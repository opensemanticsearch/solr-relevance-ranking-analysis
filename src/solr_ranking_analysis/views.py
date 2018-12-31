from django.shortcuts import render

from django.http import HttpResponse 
from django.shortcuts import render
from django import forms

import json
import requests


class SearchForm(forms.Form):

	query = forms.CharField(widget=forms.TextInput, label="Solr request URL (full Solr select query)", required=False)


# set other than the first children of max off to inactive
# for later analysis on "max of" only first (max) child
def maxof(data, results = [], parent=0):

	parent_type = None

	# get type of parent
	for entry in data:

		if entry['linenumber'] == parent:
			if 'type' in entry:
				parent_type = entry['type']

	max_score = 0
	max_scored_child = None

	# get highest scored child
	for entry in data:

		if entry['parentline'] == parent:
			if entry['numvalue'] > max_score:
				max_score = entry['numvalue']
				max_scored_child = entry['linenumber']

	# set inactive children to inactive and append all to results    
	for entry in data:

		if entry['parentline'] == parent:

			# set all childs except the highest scored to inactive
			if parent_type == "max":

				if not entry['linenumber'] == max_scored_child:
					entry['inactive'] = True

			results.append(entry)

			# recursive analysis of children
			data, results = maxof(data, results, parent=entry['linenumber'])

	return data, results


def scale_score(fullsize, value, maxvalue):

	scaled = round( fullsize/maxvalue * ( value ), 0)

	print ('full: {}, value: {}, maxvalue: {}, scaled: {}'.format(fullsize, value, maxvalue, scaled))

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
			if node['type'] == 'weight' and not 'inactive' in node:

				summarized_score += node['numvalue']

				boost, idf, tfNorm = get_scorevalues(nodes, node['linenumber'])
				fieldname = node['fieldname']
				data = {}
				data['term'] = node['term']
				data['fieldname'] = node['fieldname']

				if fieldname in fields:
					data['fieldcolor'] = fields[fieldname]['color']
				data['score'] = round( node['numvalue'], 2)
				data['score_scaled'] = scale_score(fullsize=800, value=node['numvalue'], maxvalue=maxscore)
				data['boost'] = boost
				data['idf'] = idf
				data['tfNorm'] = tfNorm

				summarization.append(data)


	#if round(summarized_score,4) < round(score,4):
	#summarization.append( "\n\nWarning: This summarization does not include all scoring factors, since more complex ranking f.e. by additioal functions like custom boostfunction(s). Please analyze all weights by tree view.\n" )
	#summarization.append( "Summarized score of full score: Only {} of {} summarized".format(summarized_score, score) )


	return summarization


def summarize_fields(nodes,fields={}):

	colors = ['#00ff00', '#ffff00']

	for node in nodes:
		if 'type' in node:
			if node['type'] == 'weight' and not 'inactive' in node:

				fieldname = node['fieldname']
				if not fieldname in fields:

					fields[fieldname] = {}

					boost, idf, tfNorm = get_scorevalues(nodes, node['linenumber'])

					fields[fieldname]['boost'] = boost
					colorindex = len(fields)-1
					if colorindex > len(colors)-1:
						colorindex = len(colors)-1

					fields[fieldname]['color'] = colors[colorindex]

	return fields

def index(request):

	form = SearchForm(request.GET) # A form bound to the POST data
	if form.is_valid():
		query = form.cleaned_data['query']


	numFound = None
	docs = None
	explain = None
	parsed_query = None
	count_docs = 0
	fields = None

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
    
					if ' = weight(' in line:
    	                
						data['type'] = 'weight'
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
			fields = summarize_fields(nodes=analyzed_results, fields=fields)
			doc_summarization = summarize(analyzed_results, fields, maxscore)
    
			doc_analysis = {}
    
			doc_analysis['id'] = doc['id']
			doc_analysis['summarization'] = doc_summarization
    
			doc_analysis['score'] = round(score ,2)
			doc_analysis['explain'] = docexplain
    
			docs.append(doc_analysis)
    
	return render(request, 'solr_ranking_analysis/solr_ranking_analysis.html', 
    		{
    			"numFound": numFound,
    			"docs": docs,
    			"explain": explain,
    			"query": query,
    			"parsed_query": parsed_query,
    			"count_docs": count_docs,
    			"form": form,
                "fields": fields,
    		})
