# Debug Toolbars

Many frameworks provide debug toolbar add-ons. `stories` integrate with
these toolbars to show the execution path and context variables of all
business objects triggered by the framework handler.

## Django contrib

Add this lines to your developer's settings:

```python
from debug_toolbar.settings import PANELS_DEFAULTS

INSTALLED_APPS = [
    "debug_toolbar",
    "stories.contrib.debug_toolbars.django",
    ...,
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    ...,
]

DEBUG_TOOLBAR_PANELS = PANELS_DEFAULTS + [
    "stories.contrib.debug_toolbars.django.panels.StoriesPanel"
]
```

You should see `stories` panel in your debug toolbar:

![Django Debug Toolbar](https://raw.githubusercontent.com/dry-python/dry-python.github.io/develop/slides/pics/debug-toolbar.png)

## Flask contrib

To show a stories panel in flask_debugtoolbar, add the panel to the
DEBUG_TB_PANELS config variable before initializing
`DebugToolbarExtension`:

```python
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)
app.config['DEBUG_TB_PANELS'] = (
    'flask_debugtoolbar.panels.versions.VersionDebugPanel',
    # ...
    'stories.contrib.debug_toolbars.flask.panels.StoriesPanel'
)
debug_toolbar = DebugToolbarExtension(app)
```
