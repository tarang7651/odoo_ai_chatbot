from odoo import release
from odoo.exceptions import ValidationError

from . import controllers
from . import models

import logging
_logger = logging.getLogger(__name__)

def pre_init_check(env):
    """Pre-init hook to ensure the module is only installed on Odoo 19."""
    major_version = int(release.version_info[0])
    _logger.info("\n\n\n\n\n\n\nPre-init check for Odoo version: %s", major_version)
    if major_version != 19:
        raise ValidationError(
            "This module is only compatible with Odoo 19. "
            f"You are running Odoo {release.version}."
        )
