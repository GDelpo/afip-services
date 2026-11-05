import os
import tempfile

# INTENTIONAL: afip_services configures logging at import time and creates
# LOG_DIR_PATH; point it at a temp dir before the package is imported.
os.environ["LOG_DIR_PATH"] = tempfile.mkdtemp(prefix="afip-services-logs-")
os.environ.pop("LOGTAIL_TOKEN", None)
os.environ.pop("AFIP_SERVICES_CATALOG", None)
