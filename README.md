Solr Relevance Ranking Analysis and Visualization Tool
======================================================

This Open Source tool and Python Django based web user interface for easier Solr Relevancy analysis helps on search relevance tuning and relevancy ranking debugging.

Therefore the tool summarize and visualize the field boosts, term weights and function queries of documents found by an Apache Solr search query.


Usage
=====

- Copy the full Solr query (URL) to the field "Query" of the form in the web user interface (UI) and click on "Analyze relevance ranking"


Configuration
=============

- Create the config file /etc/opensemanticsearch/apps/relevance_ranking_analysis/config.json (or copy the default config from the package to this destination).

- Set your Solr server and core(s) URL(s) in option "solr" in config.json

If you config only full select URL(s) for all Solr cores instead of only the Solr server URL, the tool can not misused as a HTTP proxy to the Solr API.

Example:

{
    "solr": ["http://localhost:8983/solr/opensemanticsearch/select", "http://localhost:8983/solr/opensemanticsearch-entities/select"],
}


- Optional you can set custom title field(s) in option "title_fields" in config.json to see not only terms matching the search query and ID of found documents, but the title, too (if (one of the) field(s) is returned by Solr query results)

Example:

{
    "solr": ["http://localhost:8983/solr/opensemanticsearch/select", "http://localhost:8983/solr/opensemanticsearch-entities/select"],
    "title_fields": ["title", "titles", "title_s", "title_ss", "title_txt"]
}


Installation
============


Django standalone app server
----------------------------

To use port 8000 and to listen on all configured server IPs (0) run:

python3 manage.py runserver 0:8000


Existing Django web server environment
--------------------------------------

- Copy ./src/solr_relevance_ranking_analysis to your Django apps directory
- Add "solr_relevance_ranking_analysis" to the option "INSTALLED_APPS" in your existing settings.py

