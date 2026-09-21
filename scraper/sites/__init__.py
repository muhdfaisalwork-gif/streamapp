"""
Adapter registry for all 10 StreamApp reference sites.
"""
from typing import Dict, List
from .base import BaseSiteAdapter
from .movieboxhd import MovieBoxHdAdapter
from .hdobox import HdoBoxAdapter
from .beetv import BeeTvAdapter
from .movies123 import Movies123Adapter
from .donkey import DonkeyAdapter
from .tmovies_qmovies import TMoviesAdapter
from .onstream import OnStreamAdapter
from .yify import YifyAdapter
from .yts import YtsAdapter
from .uflix import UflixAdapter

ADAPTER_CLASSES = [
    MovieBoxHdAdapter,
    HdoBoxAdapter,
    BeeTvAdapter,
    Movies123Adapter,
    DonkeyAdapter,
    TMoviesAdapter,
    OnStreamAdapter,
    YifyAdapter,
    YtsAdapter,
    UflixAdapter
]

# Singleton registry
ADAPTER_MAP: Dict[str, BaseSiteAdapter] = {
    cls.name.lower(): cls() for cls in ADAPTER_CLASSES
}

def get_adapter(name: str) -> BaseSiteAdapter | None:
    return ADAPTER_MAP.get(name.lower())

def list_adapters() -> List[str]:
    return [cls.name for cls in ADAPTER_CLASSES]

def get_all_adapters() -> List[BaseSiteAdapter]:
    return list(ADAPTER_MAP.values())
