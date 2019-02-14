Solr Relevance Ranking Analysis and Visualization Tool
======================================================

This Open Source tool and Python Django based web user interface for easier Solr Relevancy analysis helps on search relevance tuning and relevancy ranking debugging.

Therefore the tool summarize and visualize the field boosts, term weights and function queries of documents found by an Apache Solr search query.


Usage
=====

- Open the web user interface (UI) on the server/port you run the Django App (default 8000) or Docker container (see section "Installation").
- Copy the full Solr query (URL) to the field "Query" of the form in the web user interface (UI)
- Click the button "Analyze relevance ranking"


Configuration
=============

Config file
-----------

Create the config file /etc/opensemanticsearch/apps/relevance_ranking_analysis/config.json (or copy the default config or skeleton from the repository to this destination).


Solr server settings
--------------------

Set your Solr server and core(s) URL(s) in option "solr" in config.json

If you config only full select URL(s) for all Solr cores instead of only the Solr server URL, the tool can not misused as a HTTP proxy to the Solr API.

Example:

{
    "solr": ["http://localhost:8983/solr/opensemanticsearch/select", "http://localhost:8983/solr/opensemanticsearch-entities/select"],
}


Title fields (optional)
-----------------------

Optional you can set custom title field(s) in option "title_fields" in config.json to see not only terms matching the search query and ID of found documents, but the title, too (if (one of the) field(s) is returned by Solr query results)

Example:

{
    "solr": ["http://localhost:8983/solr/opensemanticsearch/select", "http://localhost:8983/solr/opensemanticsearch-entities/select"],
    "title_fields": ["title", "titles", "title_s", "title_ss", "title_txt"]
}


Installation
============

You can run this web app in a Docker container or run it by Python 3 as standalone app (using the Django web server) or integrate it to an existent web server environment running Django.


Docker
------

Setup your Solr settings to the config file /etc/opensemanticsearch/apps/relevance_ranking_analysis/config.json like described in section "Config" below.

If you don't want to build the Docker image yourself from sources (see section "Build"), the docker image will be downloaded automatically from the Docker repository of Open Semantic Search:

If your Solr server runs on another host / IP, run the Docker container for example on port 8080 (the Docker image internally provides the web server of the app on Port 8000) and your local config file by

docker run -p 8080:8000 -v /etc/opensemanticsearch/apps/relevance_ranking_analysis/config.json:/etc/opensemanticsearch/apps/relevance_ranking_analysis/config.json opensemanticsearch/solr_relevance_ranking_analysis

If your Solr server runs on localhost, you have to use --network host and the default Port 8000 instead of published port config (or change the Django port in a custom docker image build by config file "Dockerfile"):

docker run --network host -v /etc/opensemanticsearch/apps/relevance_ranking_analysis/config.json:/etc/onsemanticsearch/apps/relevance_ranking_analysis/config.json opensemanticsearch/solr_relevance_ranking_analysis


Standalone app (Python Django web server)
-----------------------------------------


- Checkout this repository by

git clone https://github.com/opensemanticsearch/solr-relevance-ranking-analysis.git

- Setup your Solr settings to the config file /etc/opensemanticsearch/apps/relevance_ranking_analysis/config.json like described in section "Config" below.

- Change to the directory with the preconfigured Django environment

cd solr-relevance-ranking-analysis/src

- To use port 8000 and to listen on all configured server IPs (0) just run:

python3 manage.py runserver 0:8000


Existing web server environment running Django
----------------------------------------------

- Checkout this repository by git clone https://github.com/opensemanticsearch/solr-relevance-ranking-analysis.git

- Setup your Solr settings to the config file /etc/opensemanticsearch/apps/relevance_ranking_analysis/config.json like described in section "Config" below.

- Copy the app directory solr-relevance-ranking-analysis/src/solr_relevance_ranking_analysis to your Django apps directory

- Add "solr_relevance_ranking_analysis" to the option "INSTALLED_APPS" in your existing settings.py


Build
=====

Docker
------

If you want to build the docker image yourself from sources:

- Checkout this repository by

git clone https://github.com/opensemanticsearch/solr-relevance-ranking-analysis.git

- Build the docker image by

docker build --tag solr_relevance_ranking_analysis solr-relevance-ranking-analysis
