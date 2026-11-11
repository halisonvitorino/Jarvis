"""Ponto de entrada: python -m jarvis"""

import sys

from jarvis.core.bootstrap import bootstrap
from jarvis.core.errors import ConfigurationError, JarvisError
from jarvis.core.logger import get_logger


def main() -> int:
    try:
        bootstrap()
    except ConfigurationError as exc:
        # Logs ainda não estão configurados quando a configuração falha.
        print(exc, file=sys.stderr)
        return 1
    except JarvisError:
        get_logger("main").exception("Falha na inicialização")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
