'''This site uses :mod:`django.contrib.flatpages` for site HTML content
that may need to be edited or maintained by site administrators.

The site is configured to use :class:`django.contrib.flatpages.middleware.FlatpageFallbackMiddleware`,
so that any page not served by the configured urls in the application that are
present in the flatpages will be displayed.  In addition, several views
(such as :meth:`belfast.groupsheets.views.list_groupsheets` or
:meth:`belfast.network.views.group_people`) search for a flatpage matching
the url and pass it for display to the view template, as preliminary or
additional text content.

The :mod:`belfast.pages` consists only of a single view for the site home
page, south migrations to load preliminary content for all flat pages that
are expected to exist when the site is deployed, and a fixture directory for
initial html content for those flat pages.

'''