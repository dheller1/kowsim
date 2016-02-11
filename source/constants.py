MM_TO_IN = 1. / 25.4
IN_TO_MM = 25.4


MOUSE_DEFAULT = 0
MOUSE_ROTATE_UNIT = 1
MOUSE_ALIGN_TO = 2
MOUSE_PLACE_UNIT = 3
MOUSE_CHECK_ARC = 4
MOUSE_CHECK_DIST = 5
MOUSE_PLACE_TERRAIN = 6
MOUSE_ROTATE_TERRAIN = 7
MOUSE_MOVE_TERRAIN = 8


ARC_FRONT = 0
ARC_REAR = 1
ARC_LEFT = 2
ARC_RIGHT = 3

# BUG: UNITS ARE STILL STACKED ON TOP OF EACH OTHER, WHICH MEANS THAT MARKERS ASSOCIATED TO THE "LOWER" UNIT ARE STILL LOWER THAN THE "UPPER" UNIT, EVEN IF THE
# MARKERS HAVE HIGHER Z VALUES THAN THE UPPER UNIT ITSELF.
Z_DIST_MARKER = 14
Z_ARC_TEMPLATE = 13
Z_MOVEMENT_TEMPLATE = 12
Z_UNIT_MARKER = 11
Z_UNIT = 10
Z_TERRAIN = 8
Z_BACKGROUND = 0