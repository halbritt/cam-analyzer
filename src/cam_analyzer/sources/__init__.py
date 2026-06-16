"""Source layer — producers of CamProfiles.

Anything here may import whatever it needs to parse its input (PDF, CSV, OCR,
measured-data formats). **Nothing here may be imported by cam_analyzer.analysis**
(C1/D001); that rule is enforced by tests/test_architecture_boundary.py.
"""
