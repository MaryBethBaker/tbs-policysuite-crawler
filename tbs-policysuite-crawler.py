# coding: utf-8

"""
tbs-policysuite-crawler
~~~~~~~~~~~~~~~~~~~~~~~

Crawls the TBS policy suite and returns a list of policy documents.

Copyright: © 2014 Thomas Gohard
Licence: MIT, see LICENSE for details

"""

__title__ = 'tbs-policysuite-crawler'
__version__ = '0.1-dev'
__author__ = 'Thomas Gohard'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014 Thomas Gohard'



import string
import re
import csv
import requests
from bs4 import BeautifulSoup
from urlparse import urlparse
from urlparse import parse_qs



"""
crawler settings
--------

_encoding:			String encoding to use for output.
_output_file:		Default file path to output the list of documents to.
_output_fields:		Fields to output in the output file.

_index_url:			URL of the policy suite index page.
_doc_url:			URL of the policy suite document page.
_indices:			List of the indices of the policy suite and of their query
					parameters.
_document_types:	List of the types of documents published in the policy
					suite. Must match the values for the "document_type" index.
_doc_link_pattern:	Regular expression matching the `id` attribute of the links
					to documents in the policy suite index page.
_doc_param:			Parameter for specifying the document to view on the policy
					suite document page.
"""

_encoding = "utf-8"
_output_file = "tbs-policies.csv"
_output_fields = ["ID", "Name", "Type"]

_index_url = "http://www.tbs-sct.gc.ca/pol/index-eng.aspx"
_doc_url = "http://www.tbs-sct.gc.ca/pol/doc-eng.aspx"
_indices = {"alphabetical": "l", "document_type": "tree"}
_document_types = ["framework", "policy", "directive", "standard", "guideline"]
_doc_link_pattern = "ctl00_CPHContent_index1_policytree1_listOfInstruments_ctl\d{2}_PolicyInstrument"
_doc_param = "id"



"""
helper functions
----------------
"""

def get_document_id(url):
	"""Get the ID of a document from the document URL's query string.

	Parameters:
		url:	A string containing the document's URL.

	Returns:
		A string containing the ID of the document.
	"""
	url_components = urlparse(url)
	qs = parse_qs(url_components.query)

	return qs[_doc_param][0]


def get_document_type(document_name):
	"""Get the type of document from the document's name.

	Parameters:
		document_name:	A string containing the document's name.

	Returns:
		A string containing a document type from _document_types or None.
	"""
	for document_type in _document_types:
		if bool(re.search(document_type, document_name, re.IGNORECASE)):
			return document_type

	return None


def parse_document_links(links, type = None):
	"""Parses a list of link elements into a dictionary of documents.

	Parameters:
		links:	A list of links to parse.
		type:	(optional) The type of documents contained in links.

	Returns:
		A dictionary of documents keyed by document ID.
	"""
	docs = {}

	for link in links:
		document_id = get_document_id(link['href'])
		document_name = link.contents[0].encode(_encoding)
		document_type = type

		if document_type is None:
			document_type = get_document_type(document_name)

		docs[document_id] = {"ID": document_id, "Name": document_name, "Type": document_type}

	return docs



"""
main functions
--------------
"""

def get_document_list(index, subset):
	"""Get a list of documents from the specified index

	Parameters:
		index:	Type of index to return. Must be one of the keys in _indices.
		subset:	Subset of the index to return. If the index type is
				alphabetical, subset must be a letter of the alphabet or the
				number '1'. If the index type is by document type, subset must
				be one of the values in _document_types.

	Returns:
		A dictionary of the documents in the specified index.
	"""
	url = _index_url + "?" + index + "=" + subset

	r = requests.get(url)
	if r.status_code != 200:
		print str(r.status_code) + ": " + r.url
		return None

	soup = BeautifulSoup(r.text)
	doc_links = soup.find_all(id=re.compile(_doc_link_pattern, re.IGNORECASE))
	docs = parse_document_links(doc_links)

	return docs


def output_as_csv(docs):
	"""Output the list of documents as comma-separated values

	Parameters:
		docs:	A dictionary of the documents to output.

	Returns:
		Nothing.
	"""
	with open(_output_file, 'w') as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames = _output_fields, delimiter = ",", quotechar = "\"", quoting = csv.QUOTE_NONNUMERIC)

		writer.writeheader()
		for doc in docs:
			writer.writerow(docs[doc])
	csvfile.close()



"""
main code
---------
"""
docs = {}

# Build alphabetical index subsets (uppercase letters of the alphabet and the number '1')
alpha_subsets = list(string.ascii_uppercase)
alpha_subsets.insert(0, "1")

for subset in alpha_subsets:
	docs.update(get_document_list(_indices["alphabetical"], subset))

for document_type in _document_types:
	docs.update(get_document_list(_indices['document_type'], document_type))

output_as_csv(docs)
