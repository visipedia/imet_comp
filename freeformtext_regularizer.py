#!/usr/bin/env python

"""

sudo pip install -U nltk
sudo pip install -U anytree
must run nltk.download('wordnet') --> /home/$USER/nltk_data

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import collections
import csv
import itertools 
from anytree import NodeMixin, RenderTree
from nltk.corpus import wordnet


class WordNode(NodeMixin):
  next_uid = itertools.count().next
  def __init__(self, name, origin_text, parent=None):
  	super(WordNode, self).__init__()
	self.name = name
	self.origin_text = origin_text
	self.parent = parent
	self.uid = WordNode.next_uid()


def _print_word_tree(root):
  """"""
  for pre, _, node in RenderTree(root):
    text = "%s%s " % (pre, node.name)
    if node.origin_text is not None:
      text += "(%s)" % node.origin_text
    print(text)


def _add_descendents_to_tree(descendents, node_map, parent):
  """"""
  if len(descendents) == 0:
  	return

  node_text = descendents.pop().name()
  
  if not node_text in node_map:
	# Create node and add it to map of all nodes.  
	node_map[node_text] = WordNode(name=node_text, origin_text=None,
		                           parent=parent)

  # Recurse.
  _add_descendents_to_tree(descendents, node_map, node_map[node_text])


def _create_ontologies(key_to_labels):
  """Synset groups are flattened.  

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
		  descendents = list(synset.closure(lambda s: s.hypernyms()))
		  _add_descendents_to_tree(collections.deque(descendents), node_map, None)

		  # Finally, add the leaf node.
		  leaf_parent = (None if len(descendents) == 0 
		  	                  else node_map[descendents[0].name()])
		  node_map[leaf_text] = WordNode(name=leaf_text, origin_text=label,
		  	                             parent=leaf_parent)

		  # If we haven't seen this tree before, keep track of the root.
		  root_node = node_map[leaf_text if len(descendents) == 0 
		                                 else descendents[-1].name()]
		  if not root_node in roots:
		  	roots.append(root_node)
  	  	else:
  	  	  # Ensure that the tree node was marked as a leaf to some label.
  	  	  node_map[leaf_text].is_original = True 

  	  	# Associate the key to the UID of the label's synset.
  	  	key_to_node_uids[key].append(node_map[leaf_text].uid)

  return node_map, roots, key_to_node_uids, not_found


def _extract_and_parse_csv(input_csv, key_header_label, values_header_label):
  """Extracts two columns from the given CSV file.

  """
  freeform_labels = {}

  with open(input_csv, 'rb') as csvfile:
    reader = csv.reader(csvfile)

    # Parse the header row.
    header = reader.next()
    key_idx = header.index(key_header_label)
    val_idx = header.index(values_header_label)

    # Parse the data rows.
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

      freeform_labels[row[key_idx]] = text

  return freeform_labels


def parse_args():
  parser = argparse.ArgumentParser(description='Free text cleaner')
  parser.add_argument('--input_csv')
  parser.add_argument('--key_header_label')
  parser.add_argument('--values_header_label')

  args = parser.parse_args()
  return args


def main():
  args = parse_args()
  freeform_labels = _extract_and_parse_csv(args.input_csv, args.key_header_label,
                                          args.values_header_label)
  node_map, roots, key_to_node_uids, not_found = _create_ontologies(freeform_labels)
  
  for root in roots:
  	_print_word_tree(root)

  print(not_found)

  # anytree io: http://anytree.readthedocs.io/en/latest/exporter/jsonexporter.html


if __name__ == "__main__":
  main()



