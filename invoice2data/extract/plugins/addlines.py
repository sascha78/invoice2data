"""
Plugin to extract individual lines from an invoice.

Initial work and maintenance by Holger Brunn @hbrunn
"""

import os
import re
import logging as logger

DEFAULT_OPTIONS = {
    'field_separator': r'\s+',
    'line_separator': r'\n',
}

def extract(self, content, output):
    """Try to extract additional lines from the invoice"""

    # First apply default options.
    plugin_settings = DEFAULT_OPTIONS.copy()
    plugin_settings.update(self['addlines'])
    self['addlines'] = plugin_settings

    # Validate settings
    assert 'add_start' in self['addlines'], 'Lines start regex missing'
    assert 'add_end' in self['addlines'], 'Lines end regex missing'
    assert 'add_line' in self['addlines'], 'Line regex missing'

    start = re.search(self['addlines']['add_start'], content)
    end = re.search(self['addlines']['add_end'], content)
    if not start or not end:
        logger.warning('no lines found - start %s, end %s', start, end)
        return
    content = content[start.end():end.start()]
    lines = []
    current_row = {}
    if 'add_first_line' not in self['addlines'] and\
            'add_last_line' not in self['addlines']:
        self['addlines']['add_first_line'] = self['addlines']['add_line']
    for line in re.split(self['addlines']['line_separator'], content):
        # if the line has empty lines in it , skip them
        if not line.strip('').strip('\n') or not line:
            continue
        if 'add_first_line' in self['addlines']:
            match = re.search(self['addlines']['add_first_line'], line)
            if match:
                if 'add_last_line' not in self['addlines']:
                    if current_row:
                        lines.append(current_row)
                    current_row = {}
                if current_row:
                    lines.append(current_row)
                current_row = {
                    field: value.strip() if value else ''
                    for field, value in match.groupdict().items()
                }
                continue
        if 'add_last_line' in self['addlines']:
            match = re.search(self['addlines']['add_last_line'], line)
            if match:
                for field, value in match.groupdict().items():
                    current_row[field] = '%s%s%s' % (
                        current_row.get(field, ''),
                        current_row.get(field, '') and '\n' or '',
                        value.strip() if value else ''
                    )
                if current_row:
                    lines.append(current_row)
                current_row = {}
                continue
        match = re.search(self['addlines']['add_line'], line)
        if match:
            for field, value in match.groupdict().items():
                current_row[field] = '%s%s%s' % (
                    current_row.get(field, ''),
                    current_row.get(field, '') and '\n' or '',
                    value.strip() if value else ''
                )
            continue
        logger.debug(
            'ignoring *%s* because it doesn\'t match anything', line
        )
    if current_row:
        lines.append(current_row)

    types = self['addlines'].get('types', [])
    for row in lines:
        for name in row.keys():
            if name in types:
                row[name] = self.coerce_type(row[name], types[name])

    if lines:
        output['addlines'] = lines
