import logging
from django.db import models
from django.utils.text import slugify
import rdflib

from belfast.util import rdf_data
from belfast.people.rdfmodels import RdfPerson

logger = logging.getLogger(__name__)


