import bleach
import mistune
from mistune.directives import RSTDirective, TableOfContents, Admonition

allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'br',
                'h1', 'h2', 'h3', 'p', 'h4', 'h5', 'h6', 'sub', 'sup', 'img', 'hr',
                'ins', 'q', 'del', 'table', 'tr', 'td',
                'mark', 'ruby', 'rp', 'rt', 'div', 'span', 'section', 'details', 'summary']

md = mistune.create_markdown(escape=False, plugins=['strikethrough', 'footnotes', 'table',
                                                    'task_lists', 'def_list', 'abbr', 'mark',
                                                    'insert', 'superscript', 'subscript', 'ruby', 'math',
                                                    RSTDirective([
                                                        TableOfContents(), Admonition()
                                                    ]),
                                                    ])

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", 'class'],
    "abbr": ["title"],
    "acronym": ["title"],
    'img': ['alt', 'title', 'src'],
    "section": ['class'],
    "p": ['class', 'id'],
    'details': ['class', 'open'],
    'ul': ['class'],
    'ol': ['class', 'start'],
    'li': ['class'],
    'h1': ['id'],
    'h2': ['id'],
    'h3': ['id'],
    'h4': ['id'],
    'h5': ['id'],
    'h6': ['id'],
    # 'h1': ['id'],

}
