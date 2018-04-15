"""
Library to create a word ontology using the anytree library.

Prereqs:
sudo pip install -U anytree
"""

import itertools
import json
from anytree import NodeMixin, RenderTree
from anytree.exporter import JsonExporter
from anytree.importer import JsonImporter


class WordNode(NodeMixin):
  """Tree node class extension."""
  generate_new_uid = itertools.count().next
  def __init__(self, name, origin_text=None, parent=None):
  	super(WordNode, self).__init__()
	self.name = name
	self.origin_text = origin_text
	self.parent = parent
	self.uid = WordNode.generate_new_uid()


def _deserialize_ontologies(filename):
  """Deserializes an ontology from a JSON file and returns its root."""
  importer = JsonImporter()
  forest = []
  with open(filename, 'r') as f:
    tree_list = json.load(f)
    for tree_text in tree_list:
      forest.append(importer.import_(tree_text))
  return forest


def _deserialize_ontology(filename):
  """Deserializes an ontology from a JSON file and returns its root."""
  importer = JsonImporter()
  return importer.read(filename)


def _extend_ontology(descendents, node_map, parent):
  """Extends an ontology (may not yet exist) from a deque of word descendents.

  Creates or extends an ontology by converting each text item to a WordNode and
  parenting them in the process. The deque of word descendents must have the
  left-right order as leaf-root. Also adds each newly created WordNode to the
  overall map of nodes.
   """
  if len(descendents) == 0:
  	return

  node_text = descendents.pop()

  if not node_text in node_map:
	# Create node and add it to map of all nodes.
	node_map[node_text] = WordNode(name=node_text, parent=parent)

  # Recurse.
  _extend_ontology(descendents, node_map, node_map[node_text])


def _print_ontology(root, uid=False):
  """Format and print a WordNode via RenderTree."""
  for pre, _, node in RenderTree(root):
    text = "%s%s " % (pre, node.name)
    if uid:
      text += "[%s] " % node.uid
    if node.origin_text is not None:
      text += "(%s)" % node.origin_text
    print(text.encode('utf-8'))


def _serialize_ontologies(roots, filename):
  """Serializes ontologies given by their roots to a JSON file.

  If no output filename is given, return the serialized as string.
  """
  exporter = JsonExporter(indent=2, sort_keys=True)
  forest = []
  for root in roots:
    forest.append(exporter.export(root))
  if not filename:
    return forest
  with open(filename, 'w') as f:
    json.dump(forest, f, indent=2, sort_keys=True)


def _serialize_ontology(root, filename=None):
  """Serializes an ontology given by its root to a JSON file.

  If no output filename is given, return the serialized as string.
  """
  exporter = JsonExporter(indent=2, sort_keys=True)
  if filename:
    exporter.write(root, filename)
  else:
  	return exporter.export(root)
