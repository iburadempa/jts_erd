# Copyright 2015 ibu radempa <ibu@radempa.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Generate an entity-relationship diagram from an extended JSON table schema.

`JSON table schema`_ is a simple schema for describing the structure of
tabular data. It can be extended to allow for a comprehensive representation
of an SQL relational database schema.

Starting from such a description this python module generates visualizations
of the database schema using `graphviz`_ via `PyGraphviz`_.

.. _`JSON table schema`: http://dataprotocols.org/json-table-schema/
.. _`graphviz`: http://graphviz.org/
.. _`PyGraphviz`: http://pygraphviz.github.io/
"""

import pygraphviz as pgv
import textwrap


options_defaults = {
    'html_color_default': '#ccff99',
    'html_color_highlight': '#33cc99',
    'fontname': 'Helvetica',
    'fontsize': 8,
    'fontsize_title': 10,
    'fontsize_label': 6,
    'bgcolor_indexes': '#ccccff',
    'rankdir': 'LR',
    'edge_thickness': 1.0,
    'display_columns': True,
    'display_indexes': True,
    'display_crowfoots': True,
    'omit_isolated_tables': False,
}
"""
Options and their default values.

Options:

  * **html_color_default**
  * **html_color_highlight**
  * **fontname**
  * **fontsize**
  * **fontsize_title**
  * **fontsize_label**
  * **bgcolor_indexes**
  * **rankdir**: 'LR' or 'RL'; whether dependent tables appear on the
    right (left) hand side
  * **edge_thickness**
  * **display_columns**: bool
  * **display_indexes**: bool
  * **display_crowfoots**: bool
  * **omit_isolated_tables**: bool  
"""


def get_graph(json_database_schema, **options):
    """
    Create and return a graph from the given *json_database_schema*.

    All keys from :any:`options_defaults` are allowed in *kwargs*.
    """
    opt = options_defaults.copy()
    opt.update(options)
    database = json_database_schema['database_name']
    datetime = json_database_schema['generation_begin_time']
    namespaces = json_database_schema['datapackages']
    schema_graph = pgv.AGraph(
        strict=False,
        directed=True,
        name='Postgres database %s (as of %s)' % (database, datetime),
        rankdir=opt['rankdir'],
        fontname=opt['fontname'],
        fontsize=opt['fontsize'],
        splines=True,
        overlap='scale'
    )

    # inventory
    present_tables = {}
    tables_with_edges = set()  # contains only tables having at least one edge
    for namespace in namespaces:
        namespace_name = namespace['datapackage']
        for table in namespace['resources']:
            present_tables[(namespace_name, table['name'])] = table
            if 'foreignKeys' in table:
                for foreign_key in table['foreignKeys']:
                    reference = foreign_key['reference']
                    tables_with_edges.add((namespace_name, table['name']))
                    tables_with_edges.add((reference['datapackage'],
                                           reference['resource']))

    # add table nodes
    for namespace in namespaces:
        namespace_name = namespace['datapackage']
        for table in namespace['resources']:
            has_edge = (namespace_name, table['name']) in tables_with_edges
            if not opt['omit_isolated_tables'] or has_edge:
                _graph_add_table(opt, schema_graph, namespace_name, table)

    # add foreign key edges
    for namespace in namespaces:
        namespace_name = namespace['datapackage']
        table_edges = set()
        for tail_table in namespace['resources']:
            tail_table_name = tail_table['name']
            if 'foreignKeys' in tail_table:
                for foreign_key in tail_table['foreignKeys']:
                    columns = foreign_key['fields']
                    if isinstance(columns, str):
                        tail_column_names = [columns]
                    else:
                        tail_column_names = columns
                    reference = foreign_key['reference']
                    head_namespace_name = reference['datapackage']
                    head_table_name = reference['resource']
                    head_column_names = reference['fields']
                    head_table = present_tables[
                        (head_namespace_name, head_table_name)
                    ]
                    enforced = foreign_key.get('enforced', True)
                    color = 'black' if enforced else 'blue'
                    card_self = reference.get('cardinalitySelf')
                    card_ref = reference.get('cardinalityRef')
                    if card_self or card_ref:
                        if opt['rankdir'] == 'RL':
                            label = '%s \u2194 %s' % (card_ref, card_self)
                        else:
                            label = '%s \u2194 %s' % (card_self, card_ref)
                    else:
                        label = ''
                    if opt['rankdir'] == 'RL':
                        tooltip = '%s     %s(%s) \u2194 %s(%s)' % (
                            label,
                            head_table_name,
                            ', '.join(head_column_names),
                            tail_table_name,
                            ', '.join(tail_column_names)
                        )
                    else:
                        tooltip = '%s     %s(%s) \u2194 %s(%s)' % (
                            label,
                            tail_table_name,
                            ', '.join(tail_column_names),
                            head_table_name,
                            ', '.join(head_column_names)
                        )
                    if reference.get('label'):
                        label += '\n' + reference.get('label')
                        tooltip += '     ' + reference.get('label')
                    else:
                        edge_name = reference.get('name')
                        if edge_name:
                            label += '   ' + edge_name
                            tooltip += '     ' + edge_name
                    label = label.strip()
                    tooltip = tooltip.strip()
                    if opt['display_columns']:
                        _add_foreign_key_edge(
                            schema_graph,
                            tail_table_name,
                            head_table_name,
                            tail_table,
                            head_table,
                            tail_column_names,
                            head_column_names,
                            label,
                            tooltip,
                            opt,
                            color,
                            card_self,
                            card_ref
                        )
                    if not opt['display_columns']:
                        table_edges.add((tail_table_name, head_table_name))
        if not opt['display_columns']:
            for tail_table_name, head_table_name in table_edges:
                schema_graph.add_edge(
                    tail_table_name,
                    head_table_name,
                    color='black'
                )
    return schema_graph


def save_svg(json_database_schema, filepath, **options):
    """
    Write an ERD in SVG format for a database to a file.

    *json_database_schema* must be compatible with what pg_jts produces.
    *filepath* must end in '.svg'.
    """
    schema_graph = get_graph(json_database_schema, **options)
    #print(schema_graph)
    # alternatives: neato, dot, twopi, circo, fdp, nop, wc, acyclic,
    #               gvpr, gvcolor, ccomps, sccmap, tred, sfdp
    schema_graph.layout(prog='dot')
    # print(schema_graph)
    schema_graph.draw(filepath)


def _graph_add_table(opt, graph, namespace_name, table,
                    default_namespace_name='public'):
    """
    Add a record-shaped node to *graph* with information on a *table*.

    All keys from `options_defaults` are allowed in *opt*.
    """
    table_name = table['name']
    table_comment = table.get('description', '')
    display = ['name', 'type', 'combined']
    title = (namespace_name + '.' if namespace_name != default_namespace_name
             else '') + table_name
    html_row0 = '<TR>\n    <TD COLOR="black" BGCOLOR="lightgrey"'\
                ' COLSPAN="%s"><FONT POINT-SIZE="%s"><b>%s</b></FONT>'\
                '<FONT POINT-SIZE="%s"><BR/>%s</FONT></TD>\n</TR>\n'\
                % (str(len(display)), opt['fontsize_title'],
                    title, opt['fontsize'], table_comment)
    html_rows = [html_row0]
    if opt['display_columns']:
        if 'primaryKey' in table:
            pk = table['primaryKey']
            for i, col_name in enumerate(pk):
                col = [c for c in table['fields'] if c['name'] == col_name][0]
                col_display = _get_column_display(display, table, col)
                table_row_html = _get_table_row_html(
                    opt, display, i + 1, col_display, highlight=True)
                html_rows.append(table_row_html)
        else:
            pk = []
        columns = [c for c in table['fields'] if c['name'] not in pk]
        #sorted_columns = sorted(columns, key=lambda c: c['pos'])
        for col_i, col in enumerate(columns):
            col_display = _get_column_display(display, table, col)
            html_row = _get_table_row_html(opt, display, col_i + len(pk) + 1,
                                           col_display)
            html_rows.append(html_row)
    if opt['display_indexes'] and 'indexes' in table:
        indexes = [i for i in table['indexes'] if not i.get('unique')]
        if indexes:
            index_definitions = ['<FONT POINT-SIZE="%s">%s</FONT>' %
                                 (opt['fontsize'], index['definition'])
                                 for index in indexes]
            html_index_definitions = '<BR/>'.join(sorted(index_definitions))
            html_row = '<TR>\n    <TD COLOR="black" BGCOLOR="%s"'\
                       ' ALIGN="LEFT" COLSPAN="%s">Extra indexes:</TD>\n'\
                       '    <TD COLOR="black" BGCOLOR="%s"'\
                       ' ALIGN="LEFT" BALIGN="LEFT">%s</TD>\n</TR>\n'\
                       % (opt['bgcolor_indexes'], str(len(display) - 1),
                          opt['bgcolor_indexes'], html_index_definitions)
            html_rows.append(html_row)
    html_table = '<TABLE ID="%s" ALIGN="LEFT" BORDER="0" CELLBORDER="0"'\
                 ' CELLSPACING="0" BGCOLOR="%s">\n%s</TABLE>'\
                 % ('table__' + table_name, 'black', ''.join(html_rows))
    label = '<\n%s\n>' % html_table
    graph.add_node(
        table_name,
        id=table_name,
        label=label,
        style='filled',
        color='white',
        fontname=opt['fontname'],
        fontsize=opt['fontsize'],
        shape='plaintext',
        tooltip=table_comment or 'Table ' + table_name
    )


def _get_column_display(display, table, column, pk=False):
    """
    Return a list of strings describing a column.

    The returned attributes and their order are given by *display*; allowed
    attributes are:

      * name
      * type
      * combined (combined str with unique constraint information,
        default value and description texts)
    """
    res = []
    for d in display:
        if d == 'name':
            res.append(column['name'])
        elif d == 'type':
            res.append(column['type'])
        elif d == 'combined':
            vals = []
            if column.get('constraints'):
                constr = column['constraints']
                if 'required' in constr:
                    vals.append(_format_attribute('null', constr['required']))
            uniques = []
            table_unique = table.get('unique')
            if table_unique:
                for t_u_i, t_u in enumerate(table_unique):
                    if column['name'] in t_u['fields']:
                        i = t_u['fields'].index(column['name'])
                        if len(t_u['fields']) == 1:
                            uniques.append('UNIQ')
                        else:
                            uniques.append('UNIQ%s:%s'
                                           % (str(t_u_i + 1), str(i + 1)))
            if column.get('constraints'):
                column_unique = column['constraints'].get('unique')
                if 'UNIQ' not in uniques and column_unique:
                    uniques.append('UNIQ')
            vals.append('; '.join(uniques))
            default_value = 'DEFAULT=' + column['default_value']\
                            if 'default_value' in column else ''
            vals.append(default_value)
            description = column.get('description', '')
            vals.append(description)
            text = '; '.join([v for v in vals if v]).replace('\n', '; ')
            wrapped_text = '<BR/>\n'.join(textwrap.wrap(text, width=50))
            res.append(wrapped_text)
    return res


def _get_table_row_html(opt, display, port, table_cols,
                        align='LEFT', highlight=False):
    """
    Return a graphviz HTML string for a table row describing a column.

    Add graphviz PORT numbers, prepedend with 'i' for the leftmost cell and
    with 'f' for the rightmost cell.
    """
    cols_html = ''
    for i, table_col in enumerate(table_cols):
        table_col = _format_attribute(display[i], table_col)
        port_ = ''
        if i == 0 and port is not None:
            port_ = ' PORT="i%s"' % str(port)
        if i == len(table_cols) - 1 and port is not None:
            port_ = ' PORT="f%s"' % str(port)
        color = (opt['html_color_highlight'] if highlight
                 else opt['html_color_default'])
        cols_html += '<TD BGCOLOR="%s" ALIGN="%s" BALIGN="%s"%s>%s</TD>'\
            % (color, align, align, port_, table_col)
    return '<TR>\n    %s\n</TR>\n' % cols_html


def _format_attribute(attribute_type, attribute_value):
    """
    Return *attribute_value*, except for special *attribute_type*s.

    For special *attribute_type*s the given string *attribute_value* is
    modified, depending on the *attribute_type*:

      * **null**
      * **name**
      * **default**
    """
    if attribute_type.lower() == 'null':
        if attribute_value:
            return ''
        else:
            return '<s>NULL</s>'
    elif attribute_type.lower() == 'name':
        return '<b>%s</b>' % attribute_value
    elif attribute_type == 'default':
        if attribute_value is not None:
            if attribute_value.lower().startswith('nextval('):
                return '[sequence]'
            else:
                return attribute_value
        else:
            return ''
    else:
        return attribute_value


def _add_foreign_key_edge(schema_graph, tail_table_name, head_table_name,
                          tail_table, head_table, tail_column_names,
                          head_column_names, label, tooltip, opt, color,
                          card_tail, card_head):
    """
    Modify *schema_graph* by adding edges (for a foreign key relation).

    For multi-column relations also intermediate nodes are added.
    """
    port_l = 'i'
    port_r = 'f'
    if opt['rankdir'] == 'RL':
        port_l = 'f'
        port_r = 'i'
    if len(tail_column_names) > 1:
        tail_agg = 'tail agg %s%s->%s' % (
            tail_table_name, str(tail_column_names), head_table_name)
        schema_graph.add_node(
            tail_agg,
            id=tail_table_name,
            label='',
            style='filled',
            color='red',
            arrowtail=None,
            arrowhead=None,
            shape='point'
        )
        for tail_column_name in tail_column_names:
            tail_port = port_r + str(_get_port(tail_table, tail_column_name))
            schema_graph.add_edge(
                tail_table_name,
                tail_agg,
                tailport=tail_port,
                penwidth=opt['edge_thickness'],
                color=color,
                dir='none'
            )
        tail_node = tail_agg
        tail_port = ''
    else:
        tail_node = tail_table_name
        tail_port = port_r + str(_get_port(tail_table, tail_column_names[0]))
    if len(head_column_names) > 1:
        head_agg = 'head agg %s->%s%s' % (
            tail_table_name, head_table_name, str(tail_column_names))
        schema_graph.add_node(
            head_agg,
            id=head_table_name,
            label='',
            style='filled',
            color='red',
            arrowtail=None,
            arrowhead=None,
            shape='point'
        )
        for head_column_name in head_column_names:
            head_port = port_l + str(_get_port(head_table, head_column_name))
            schema_graph.add_edge(
                head_agg,
                head_table_name,
                headport=head_port,
                penwidth=opt['edge_thickness'],
                color=color,
                dir='none'
            )
        head_node = head_agg
        head_port = ''
    else:
        head_node = head_table_name
        head_port = head_port = port_l + str(_get_port(head_table,
                                                       head_column_names[0]))
    schema_graph.add_edge(
        tail_node,
        head_node,
        tailport=tail_port,
        headport=head_port,
        penwidth=opt['edge_thickness'],
        color=color,
        label=label,
        fontname=opt['fontname'],
        fontsize=opt['fontsize_label'],
        fontcolor=color,
        arrowtail=_get_crowfoot(card_tail, opt),
        arrowhead=_get_crowfoot(card_head, opt),
        tooltip=tooltip,
        labeltooltip=tooltip,
        dir='both'
    )


def _get_port(table, column):
    """
    Return the port number of a table column.

    The port number is the row number in the html table, counting from 0.
    Row 0 is the row containing the table name. It is followed by
    rows describing primary key columns and then by all other columns.
    """
    if 'primaryKey' in table:
        pk = table['primaryKey']
        if column in pk:
            return int(pk.index(column)) + 1
        offset = len(pk)
    else:
        pk = []
        offset = 0
    columns_non_pk = [c['name'] for c in table['fields']
                      if c['name'] not in pk]
    return columns_non_pk.index(column) + offset + 1


def _get_crowfoot(cardinality, opt):
    """
    Return the arrow name for a crowfoot with given *cardinality*.

    Cardinalities are:

      * 0..1
      * 1
      * 0..N
      * 1..N
    """
    if not opt['display_crowfoots']:
        return 'none'
    if cardinality == '0..1':
        return 'teeodot'
    if cardinality == '1':
        return 'teetee'
    if cardinality == '0..N':
        return 'crowodot'
    if cardinality == '1..N':
        return 'crowtee'
    return 'none'
