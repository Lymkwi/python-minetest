# -*- encoding: UTF-8 -*-
##########################
## Logger for python-minetest
##
#

import logging

def init_logging(debug=False):
	logger = logging.getLogger()

	formatter = logging.Formatter("%(asctime)s %(name)s:%(funcName)-25s:%(lineno)-4s %(levelname)-8s %(message)s")

	strhandler = logging.StreamHandler()
	strhandler.setLevel(logging.DEBUG)
	strhandler.setFormatter(formatter)
	logger.addHandler(strhandler)

	if debug:
		logger.setLevel(logging.DEBUG)

logger = logging.getLogger()
