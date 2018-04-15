#!/usr/bin/env python
"""
Tool to create ontologies from a text column in a CSV file.

Each CSV row denotes a single object whose ID can be provided in a denoted
column. If not provided, the row number will be used instead.

The CSV column containing the free-form text is presumably a list of terms
delimited by either a semi-colon or a new-line character.

For each free-form label, its closest match is found in WordNet. For each
WordNet match, its ontology is created.

The output contains the created ontologies where each node contains a unique
ID (UID) and its originating query text from the CSV file.

The secondary output contains a mapping of each CSV row or object that had a
WordNet mapping to a list of corresponding UIDs in the ontologies.

Prereqs:
sudo pip install -U nltk
must run nltk.download('wordnet') --> /home/$USER/nltk_data

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import collections
import csv
import json
import word_ontology as wo
from nltk.corpus import wordnet


def _create_ontologies(key_to_labels):
  """Creates ontologies for the given labels and tracks unfound labels.

  Creates ontologies for the given labels and tracks labels not found.
  Recreates the key to tree node unique identifiers (UIDs).

  Note that synset groups are flattened:
  If a key has N labels, and each one returns M synsets, then the object is
  associated with MN unique words, without knowing which word came from which
  label.
  """
  node_map = {}
  roots = []
  not_found = {}
  key_to_node_uids = collections.defaultdict(list)

  for key, labels in key_to_labels.iteritems():
  	for label in labels:
  	  synsets = wordnet.synsets(label)

  	  # If label is not found, keep track of it and move on.
  	  if len(synsets) == 0:
  	  	if label in not_found:
  	  	  not_found[label] += 1
  	  	else:
  	  	  not_found[label] = 1
  	  	continue

  	  # If label is found, find its tree path.
  	  for synset in synsets:
  	  	leaf_text = synset.name()

  	  	# If leaf does not exist, add it and its descendents.
  	  	if not leaf_text in node_map:
		  # Path is returned in leaf -> root order.
		  descendents = [d.name()
		                 for d in synset.closure(lambda s: s.hypernyms())]
		  wo._extend_ontology(collections.deque(descendents), node_map, None)

		  # Finally, add the leaf node.
		  leaf_parent = (None if len(descendents) == 0
		  	                  else node_map[descendents[0]])
		  node_map[leaf_text] = wo.WordNode(name=leaf_text, origin_text=label,
		  	                                parent=leaf_parent)

		  # If we haven't seen this tree before, keep track of the root.
		  root_node = node_map[leaf_text if len(descendents) == 0
		                                 else descendents[-1]]
		  if not root_node in roots:
		  	roots.append(root_node)

  	  	# Associate the key to the UID of the label's synset.
  	  	key_to_node_uids[key].append(node_map[leaf_text].uid)

  return roots, key_to_node_uids, not_found


def _extract_and_parse_csv(input_csv, key_header_label, values_header_label):
  """Extracts two columns from the given CSV file given the header row keys."""
  freeform_labels = {}

  with open(input_csv, 'rb') as csvfile:
    reader = csv.reader(csvfile)

    # Parse the header row.
    header = reader.next()
    key_idx = (None if key_header_label is None
    	            else header.index(key_header_label))
    val_idx = header.index(values_header_label)

    # Parse the data rows.
    row_idx = 2
    for row in reader:
      text = row[val_idx].decode('utf-8').lower()
      if len(text) == 0:
        continue

      # Only one type of delimiter is expected in the free-form text field.
      if text.find(';') != -1 and text.find('\n') != -1:
        raise ValueError('Free-form text field cannot contain both '';'' and '
                         'newline delimiters.')

      # Parse if necessary.
      if text.find(';') != -1:
        text = text.split(';')
      elif text.find('\n') != -1:
        text = text.splitlines()
      else:
        text = [text]

      freeform_labels[row_idx if key_idx is None else row[key_idx]] = text
      row_idx += 1

  return freeform_labels


def parse_args():
  parser = argparse.ArgumentParser(description='Free text cleaner')
  parser.add_argument('--input_csv',
  					  help='Path to input CSV file.',
  	                  required=True)
  parser.add_argument('--key_header_label',
  	 				  help='Text in column header of input CSV file denoting '
  	 				  'column with presumably unique IDs to key the output '
  	 				  'map. If not provided, the row number will be used '
  	 				  'instead.',
  	 				  default=None)
  parser.add_argument('--values_header_label',
  	                  help='Text in column header of input CSV file denoting '
  	                  'column with text to regularize.',
  	                  required=True)
  parser.add_argument('--output_json_ontologies',
  					  help='Path to output JSON file of resolved ontologies.',
  					  required=True)
  parser.add_argument('--output_json_key_to_ontology_uid_map',
  	                  help='Path to output JSON file of keys or unique IDs '
  	                  'from the CSV file to the unique IDs of words in the '
  	                  'resolved ontologies.',
  	                  required=True)

  args = parser.parse_args()
  return args


def main():
  args = parse_args()
  key_to_freeform_labels = _extract_and_parse_csv(
  	  args.input_csv, args.key_header_label, args.values_header_label)
  roots, key_to_node_uids, not_found = _create_ontologies(
  	  key_to_freeform_labels)

  print('Ontologies found:')
  for root in roots:
  	wo._print_ontology(root)
  	print("\n")
  wo._serialize_ontologies(roots, args.output_json_ontologies)
  print('Ontologies written to %s' % args.output_json_ontologies)

  print('\nFree-form text not found (with counts):')
  print(not_found)

  with open(args.output_json_key_to_ontology_uid_map, 'w') as f:
    json.dump(dict(key_to_node_uids), f,
    	      args.output_json_key_to_ontology_uid_map, indent=2,
    	      sort_keys=True)
  print('\nKey-to-ontology-UIDs map written to %s' %
  	    args.output_json_key_to_ontology_uid_map)

if __name__ == '__main__':
  main()



