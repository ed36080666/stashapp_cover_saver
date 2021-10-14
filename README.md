# StashApp Cover Saver


StashApp plugin to save local copies of scene covers. Hooks into the `Scene.Updated.Post` event and saves a local copy of a cover image being set (if one does not already exist for the scene locally).

Currently this is only working with images set via scraping or manually via file/url. The generation of thumbnails from screen does not emit the `Scene.Updated.Post` event and will not trigger the plugin.

todo: more info...
