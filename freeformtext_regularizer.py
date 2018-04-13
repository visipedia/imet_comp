#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import csv
from nltk.corpus import wordnet

def extract_and_parse_csv(input_csv, key_header_label, values_header_label):
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
  freeform_labels = extract_and_parse_csv(args.input_csv, args.key_header_label,
                                          args.values_header_label)
  print(freeform_labels)


if __name__ == "__main__":
  main()



