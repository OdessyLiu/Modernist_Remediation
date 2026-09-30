#!/usr/bin/env python3
"""Compatibility entry point for the combined XML corpus exporter.

Run either this script or Reviews_XMLCorpus.py to create the full corpus and
high/low/middle/unrated XML subsets. --output now specifies the full XML file.
Existing JSON and plain-text exports are retained but are no longer regenerated.
"""

from Reviews_XMLCorpus import main


if __name__ == "__main__":
    main()
